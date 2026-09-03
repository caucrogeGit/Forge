# pyright: strict
"""Routes HTTP des notifications (`NOTIF-HTTP-ROUTES-001`).

Le paquet savait écrire une notification et la relire depuis Python. Il
n'exposait **aucune route**, là où `forge-mvc-video` livre
`register_video_routes` et `forge-mvc-iot` livre `register_iot_routes`.

Chaque application devait donc écrire son contrôleur, sa sérialisation JSON et
son compteur de non-lus avant de pouvoir afficher quoi que ce soit. Mesuré sur
une application réelle : elle écrivait des notifications depuis des mois et
n'en avait jamais affiché une seule, ayant buté sur cette marche manquante.

## Le destinataire vient de la session, jamais de la requête

C'est le point qui décide de tout le reste.

Un destinataire est une chaîne libre, `professeur.42`, et Forge ne sait pas la
dériver d'une session : la convention appartient à l'application. Elle fournit
donc un résolveur, et **son absence empêche l'enregistrement des routes**,
plutôt que de laisser une route lire un destinataire passé en paramètre.

Accepter `?recipient=professeur.7` donnerait à quiconque les notifications de
n'importe qui. Ce n'est pas une précaution théorique : c'est la première chose
qu'on écrit quand on veut aller vite.

## Le rafraîchissement appartient à l'application

Ces routes rendent du JSON. Elles ne poussent rien, n'ouvrent aucune connexion
longue, et ne fournissent aucun script.

Un écran qui se met à jour tout seul s'écrit avec HTMX, que Forge livre déjà :

    <span hx-get="/api/notifications/unread-count"
          hx-trigger="every 10s" hx-swap="innerHTML"></span>

Une interrogation toutes les dix secondes coûte, pour quarante écrans ouverts,
quatre requêtes par seconde servies en quelques millisecondes. Les tenir
ouvertes en SSE coûterait quarante travailleurs immobilisés.
"""
from __future__ import annotations

import logging
from typing import Any, Callable

from core.http.helpers import json_error
from core.http.response import Response

from forge_mvc_notifications.errors import NotificationError
from forge_mvc_notifications.store import (
    MAX_LIMIT,
    Notification,
    get_notifications,
    mark_all_read,
    mark_read,
    unread_count,
)

__all__ = [
    "ROUTE_UNREAD_COUNT",
    "ROUTE_LIST",
    "ROUTE_MARK_READ",
    "ROUTE_MARK_ALL_READ",
    "DEFAULT_PAGE_SIZE",
    "RecipientResolver",
    "NotificationHttpController",
    "serialize_notification",
    "register_notification_routes",
]

logger = logging.getLogger("forge.notifications")

ROUTE_UNREAD_COUNT = "/api/notifications/unread-count"
ROUTE_LIST = "/api/notifications"
ROUTE_MARK_READ = "/api/notifications/{id}/read"
ROUTE_MARK_ALL_READ = "/api/notifications/read-all"

#: Taille de page par défaut. Un panneau de notifications en montre une
#: vingtaine ; en rendre cinquante ferait payer à chaque interrogation une
#: liste que personne ne déroule.
DEFAULT_PAGE_SIZE = 20

#: L'application dit à quel destinataire correspond une requête. Rend `None`
#: quand personne n'est authentifié.
RecipientResolver = Callable[[Any], "str | None"]


def serialize_notification(notification: Notification) -> "dict[str, Any]":
    """Notification rendue en JSON.

    `recipient` en est **absent** : le client ne reçoit que ses propres
    notifications, le lui répéter à chaque ligne n'apprend rien et expose la
    convention de nommage interne de l'application.
    """
    return {
        "id": notification.id,
        "type": notification.type,
        "message": notification.message,
        "data": notification.data,
        "read": notification.read,
        "created_at": notification.created_at,
        "target_url": notification.target_url,
    }


class NotificationHttpController:
    """Handlers branchés sur le magasin de notifications."""

    def __init__(self, recipient_of: RecipientResolver, *, db: Any = None) -> None:
        self._recipient_of = recipient_of
        self._db = db

    def _recipient(self, request: Any) -> "str | None":
        """Destinataire de la requête, ou `None`.

        Un résolveur qui lève est traité comme « personne » : une session mal
        formée ne doit pas rendre 500, et surtout ne doit pas ouvrir l'accès.
        """
        try:
            valeur = self._recipient_of(request)
        except Exception:
            logger.exception(
                "Forge Notifications - le résolveur de destinataire a levé ; "
                "la requête est traitée comme non authentifiée"
            )
            return None
        if not isinstance(valeur, str):
            return None
        return valeur.strip() or None

    def unread_count(self, request: Any) -> Response:
        """Nombre de notifications non lues (`GET /api/notifications/unread-count`)."""
        destinataire = self._recipient(request)
        if destinataire is None:
            return json_error("unauthorized", 401)
        try:
            total = unread_count(destinataire, db=self._db)
        except Exception:
            logger.exception("Forge Notifications - erreur DB sur unread_count")
            return json_error("internal_server_error", 500)
        return Response.json({"data": {"count": total}})

    def list(self, request: Any) -> Response:
        """Notifications du destinataire (`GET /api/notifications`).

        `before_id` pagine par curseur, jamais par `OFFSET` : une notification
        arrivée entre deux pages décalerait tout ce qui suit, et une liste de
        notifications est justement celle qui reçoit des écritures pendant
        qu'on la parcourt (`NOTIF-PAGINATION-001`).
        """
        destinataire = self._recipient(request)
        if destinataire is None:
            return json_error("unauthorized", 401)

        limite = _entier(request, "limit", DEFAULT_PAGE_SIZE)
        if limite is None or limite < 1 or limite > MAX_LIMIT:
            return json_error("invalid_limit", 400)
        avant = _entier(request, "before_id", 0)
        if avant is None or avant < 0:
            return json_error("invalid_before_id", 400)
        non_lues = str(_query(request, "unread") or "").strip() in ("1", "true")

        try:
            lignes = get_notifications(
                destinataire,
                unread_only=non_lues,
                limit=limite,
                before_id=avant or None,
                db=self._db,
            )
        except NotificationError:
            return json_error("invalid_request", 400)
        except Exception:
            logger.exception("Forge Notifications - erreur DB sur get_notifications")
            return json_error("internal_server_error", 500)

        # Le curseur de la page suivante est l'identifiant de la dernière ligne
        # rendue. `None` quand la page n'est pas pleine : il n'y a alors rien
        # après, et rendre un curseur ferait demander une page vide.
        suivant = lignes[-1].id if len(lignes) == limite else None
        return Response.json({
            "data": {
                "notifications": [serialize_notification(n) for n in lignes],
                "next_before_id": suivant,
            }
        })

    def mark_read(self, request: Any) -> Response:
        """Marque une notification comme lue (`POST /api/notifications/<id>/read`).

        Le marquage est **borné au destinataire** : l'identifiant seul suffirait
        sinon à faire disparaître l'alerte de quelqu'un d'autre.
        """
        destinataire = self._recipient(request)
        if destinataire is None:
            return json_error("unauthorized", 401)
        try:
            identifiant = int(str(request.route("id")))
        except (TypeError, ValueError):
            return json_error("not_found", 404)

        try:
            marquee = mark_read(identifiant, recipient=destinataire, db=self._db)
        except Exception:
            logger.exception("Forge Notifications - erreur DB sur mark_read")
            return json_error("internal_server_error", 500)

        # `False` couvre deux cas indiscernables en SQL, la notification déjà
        # lue et celle d'un autre destinataire. Les distinguer demanderait une
        # lecture préalable, qui apprendrait à l'appelant qu'un identifiant
        # existe chez quelqu'un d'autre.
        return Response.json({"data": {"marked": marquee}})

    def mark_all_read(self, request: Any) -> Response:
        """Marque tout comme lu (`POST /api/notifications/read-all`)."""
        destinataire = self._recipient(request)
        if destinataire is None:
            return json_error("unauthorized", 401)
        try:
            total = mark_all_read(destinataire, db=self._db)
        except Exception:
            logger.exception("Forge Notifications - erreur DB sur mark_all_read")
            return json_error("internal_server_error", 500)
        return Response.json({"data": {"marked": total}})


def _query(request: Any, nom: str) -> "str | None":
    lecteur = getattr(request, "query", None)
    if not callable(lecteur):
        return None
    valeur = lecteur(nom)
    return None if valeur is None else str(valeur)


def _entier(request: Any, nom: str, defaut: int) -> "int | None":
    """Entier lu dans la requête, ou `None` s'il est illisible.

    `None` et non le défaut : une valeur illisible est une demande fautive, et
    la remplacer en silence rendrait une page que l'appelant n'a pas demandée.
    """
    brut = _query(request, nom)
    if brut is None or not brut.strip():
        return defaut
    try:
        return int(brut.strip())
    except ValueError:
        return None


def register_notification_routes(
    router: Any,
    *,
    recipient_of: "RecipientResolver | None" = None,
    db: Any = None,
) -> Any:
    """Enregistre les routes de notifications sur un `Router` Forge.

    Appelée **explicitement** par l'application (ADR-030, principe 9).

    `recipient_of` associe une requête au destinataire de ses notifications.
    Elle est **obligatoire** : un destinataire est une chaîne libre dont la
    convention appartient à l'application, et Forge ne peut pas la deviner.

    Son absence lève ici, à l'enregistrement, plutôt que de rendre 401 à chaque
    requête : une application qui monte ces routes sans résolveur a fait une
    erreur de câblage, et la découvrir au démarrage vaut mieux qu'en production.

    ```python
    from forge_mvc_notifications import register_notification_routes

    register_notification_routes(
        router,
        recipient_of=lambda r: (
            f"professeur.{utilisateur.id}" if (utilisateur := courant(r)) else None
        ),
    )
    ```

    Les routes ne sont **pas publiques** : le routeur exige une session, et le
    résolveur exige en plus qu'elle désigne quelqu'un. Les deux mutations sont
    en POST, donc protégées par CSRF ; un appel HTMX doit porter le jeton.
    """
    if recipient_of is None:
        raise NotificationError(
            "register_notification_routes exige recipient_of : un destinataire "
            "est une chaîne libre, « professeur.42 », dont la convention "
            "appartient à l'application. Sans résolveur, la route ne pourrait "
            "lire le destinataire que dans la requête, ce qui donnerait à "
            "quiconque les notifications de n'importe qui."
        )

    controller = NotificationHttpController(recipient_of, db=db)

    router.add(
        "GET", ROUTE_UNREAD_COUNT, controller.unread_count,
        name="notifications-unread-count", csrf=False, api=True,
    )
    router.add(
        "GET", ROUTE_LIST, controller.list,
        name="notifications-list", csrf=False, api=True,
    )
    router.add(
        "POST", ROUTE_MARK_READ, controller.mark_read,
        name="notifications-mark-read", api=True,
    )
    router.add(
        "POST", ROUTE_MARK_ALL_READ, controller.mark_all_read,
        name="notifications-mark-all-read", api=True,
    )
    return router
