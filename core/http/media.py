# pyright: strict
"""core/http/media.py — Service des médias `GET /media/...`, source unique.

Ticket : CORE-WSGI-MEDIA-PARITY-001.

`/media/` est servi **avant le routage** : c'est un préfixe, pas une route, et
le routeur de Forge n'apparie pas un chemin à segments variables.

Cette interception vivait dans le seul `RequestHandler` du squelette. Le chemin
WSGI, seul chemin de production supporté, ne la connaissait pas : une
application déployée servait ses pages et rendait **404 sur tous ses médias**.
Mesuré sur un projet engendré, le même fichier des deux côtés :

    serveur de développement          : 200
    chemin WSGI (Gunicorn)            : 404

C'est le défaut de `CORE-WSGI-HEALTH-PARITY-001`, à l'identique, et il appelle
le même remède : la réponse est définie **une fois**, et les deux serveurs la
servent. Un écart de comportement entre les deux chemins devient impossible,
puisqu'il n'y a plus deux comportements.

Le contournement évident, un `location /media/` dans la configuration Nginx,
est celui qu'il ne faut pas prendre : il rend public tout `UPLOAD_ROOT` et
retire définitivement à l'application le droit de décider qui lit quoi.

Le cœur ne nomme aucun opt-in
-----------------------------
Le service de fichiers a été extrait vers un opt-in (ADR-019), et le cœur
runtime ne cite aucun paquet opt-in dans son code. Le fournisseur est donc
**découvert par entry point**, comme les backends BDD (ADR-054) et les
commandes CLI (ADR-059), dans le groupe `forge_mvc.media_server`.

La découverte porte sur ce qui est INSTALLÉ, jamais sur ce qui a été importé :
un registre alimenté à l'import ferait dépendre le service de l'ordre des
imports du projet, et un projet dont aucun contrôleur ne touche aux fichiers
perdrait ses médias sans raison visible.

Aucun fournisseur installé : 404, exactement comme avant. Le cœur reste
utilisable sans l'opt-in, et n'acquiert aucune dépendance.

Périmètre, et c'est une limite à connaître
------------------------------------------
Ce chemin ne demande **aucune authentification**, ni ici ni sur le serveur de
développement : `/media/` est une porte publique, et cette parité ne change pas
son régime d'accès, elle le rend seulement cohérent.

Une application qui distingue des fichiers publics de fichiers personnels
(travaux d'élèves, pièces jointes, justificatifs) doit servir les seconds par
une route authentifiée, et non les déposer sous `/media/`.
"""
from __future__ import annotations

import logging
import threading
from importlib.metadata import entry_points
from typing import Any, Callable, Protocol

from core.http.response import Response

logger = logging.getLogger(__name__)

#: Préfixe des médias, tel que le servent les deux serveurs.
MEDIA_PREFIX = "/media/"

#: Groupe d'entry point des fournisseurs de médias.
ENTRY_POINT_GROUP = "forge_mvc.media_server"


class MediaServer(Protocol):
    """Contrat attendu d'un fournisseur de médias.

    `relative_path` est le chemin DÉJÀ débarrassé du préfixe `/media/`. Le
    fournisseur reste seul responsable de sa résolution anti-traversal : le
    cœur ne connaît ni la racine de stockage ni ses règles.
    """

    def __call__(self, relative_path: str, *, request: Any = None) -> Response: ...


_fournisseur: "Callable[..., Response] | None" = None
_resolu = False
_verrou = threading.Lock()


def is_media_request(path: str) -> bool:
    """Dit si `path` vise un média.

    Compare le chemin seul. L'appelant passe `request.path`, déjà débarrassé de
    la chaîne de requête.
    """
    return path.startswith(MEDIA_PREFIX)


def _not_found() -> Response:
    """Réponse d'absence, identique qu'il manque le fichier ou l'opt-in.

    Ne pas distinguer les deux est délibéré : dire à un visiteur anonyme quel
    outillage tourne sur le serveur ne l'aide en rien, et renseigne qui cherche.
    """
    return Response(404, b"Not found", "text/plain; charset=utf-8")


def _decouvrir() -> "Callable[..., Response] | None":
    """Résout le fournisseur installé, ou `None`. Le résultat est mémorisé."""
    points = sorted(entry_points(group=ENTRY_POINT_GROUP), key=lambda ep: ep.name)
    if not points:
        return None
    if len(points) > 1:
        # Anomalie d'installation. On sert quand même, de façon déterministe :
        # un 500 sur les médias serait un remède pire que le mal.
        noms = ", ".join(ep.name for ep in points)
        logger.warning(
            "Plusieurs fournisseurs de médias installés (%s) ; %s retenu.",
            noms, points[0].name)
    try:
        return points[0].load()
    except Exception:  # noqa: BLE001 — opt-in cassé : 404, jamais une 500
        logger.exception(
            "Le fournisseur de médias %s est installé mais non chargeable.",
            points[0].name)
        return None


def media_server() -> "Callable[..., Response] | None":
    """Fournisseur de médias installé, ou `None`. Résolu une seule fois."""
    global _fournisseur, _resolu
    if _resolu:
        return _fournisseur
    with _verrou:
        if not _resolu:
            _fournisseur = _decouvrir()
            _resolu = True
    return _fournisseur


def reset_media_server_cache() -> None:
    """Oublie le fournisseur mémorisé. Réservé aux tests."""
    global _fournisseur, _resolu
    with _verrou:
        _fournisseur = None
        _resolu = False


def media_response(path: str, request: Any = None) -> Response:
    """Sert le média visé par `path`, identiquement sur les deux serveurs.

    `request` est propagé pour le support HTTP Range
    (`FILES-SERVE-RANGE-DELEGATE-001`) : sans lui, le fichier part en entier.

    Toute absence, tout refus et toute erreur du fournisseur donnent un 404 :
    ce chemin est atteint par n'importe quel visiteur, avant le routage, et une
    trace d'exception n'y a rien à faire.
    """
    fournisseur = media_server()
    if fournisseur is None:
        return _not_found()

    relative_path = path[len(MEDIA_PREFIX):]
    try:
        return fournisseur(relative_path, request=request)
    except Exception:  # noqa: BLE001 — cf docstring
        logger.exception("Le service du média %r a échoué.", relative_path)
        return _not_found()
