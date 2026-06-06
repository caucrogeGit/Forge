"""
core/app/dev_server.py — Messages de diagnostic du serveur de développement
=======================================================================
Fonctions pures de mise en forme des messages affichés par app.py au démarrage
du serveur HTTP/HTTPS local.

Conçues pour être testables sans démarrer de vrai serveur ni importer app.py
(qui déclenche la configuration globale de Forge à l'import).

Périmètre strict :
    - mise en forme des messages d'aide au démarrage ;
    - mise en forme du message d'erreur quand le port est déjà utilisé.

Ne contient ni I/O, ni gestion de processus, ni détection réseau.
"""
from __future__ import annotations


def scheme_for(ssl_enabled: bool) -> str:
    """Retourne 'https' ou 'http' selon le drapeau SSL."""
    return "https" if ssl_enabled else "http"


def format_startup_messages(host: str, port: int, ssl_enabled: bool) -> list[str]:
    """
    Construit les lignes d'information affichées au démarrage.

    La première ligne reproduit le format historique
    (« Serveur en écoute sur <scheme>://<host>:<port> ») pour ne pas casser les
    scripts qui matchent cette chaîne.

    Quand host vaut 0.0.0.0, ajoute une aide explicite : URL locale, rappel que
    l'adresse réseau réelle dépend de la machine, et — si HTTPS est actif —
    rappel du protocole pour éviter la confusion http:// vs https://.
    """
    scheme = scheme_for(ssl_enabled)
    lines: list[str] = [f"Serveur en écoute sur {scheme}://{host}:{port}"]

    if host == "0.0.0.0":
        lines.append(f"Depuis cette machine : {scheme}://127.0.0.1:{port}")
        lines.append(
            "Depuis une autre machine du réseau : utilisez l'IP réelle de "
            f"cette machine, par exemple {scheme}://<IP_MACHINE>:{port}"
        )
        lines.append(
            "Rappel : 0.0.0.0 signifie « écoute sur toutes les interfaces » ; "
            "le navigateur doit utiliser une IP joignable, pas 0.0.0.0."
        )

    if ssl_enabled:
        lines.append(
            f"Attention : le serveur utilise HTTPS — préfixez bien vos URL "
            f"par {scheme}:// (le navigateur affichera un avertissement de "
            "certificat auto-signé)."
        )

    return lines


# ── Garde production / hôte public (APP-PY-PROD-HOST-GUARD-001) ─────────────
#
# `python app.py` reste un serveur de développement. En production publique,
# Forge documente `WSGI + Gunicorn + reverse proxy` comme seule voie supportée
# (cf docs/deployment/wsgi-deployment.md). Le serveur direct écoutant sur `0.0.0.0` ou
# `::` en `APP_ENV=prod` est presque toujours une mauvaise configuration —
# on refuse explicitement plutôt que d'émettre un WARN ignorable.

_DANGEROUS_PUBLIC_HOSTS: frozenset[str] = frozenset({"0.0.0.0", "::"})


def is_dangerous_public_host(host: str) -> bool:
    """True si l'hôte écoute sur toutes les interfaces (IPv4 ou IPv6).

    Reconnu (refusé en prod via le garde) :
        - "0.0.0.0"
        - "::"
        - "[::]" (forme bracketed type URL)
        - variantes avec espaces ou casse différente

    Toléré (jamais bloqué) :
        - "127.0.0.1", "localhost", "::1", "[::1]"
        - tout hostname spécifique non listé ci-dessus
    """
    normalized = (host or "").strip().strip("[]").lower()
    return normalized in _DANGEROUS_PUBLIC_HOSTS


def format_prod_host_guard_error(app_env: str, app_host: str) -> str:
    """Message d'erreur émis quand `python app.py` refuse de démarrer en
    prod sur une interface publique.

    Doit citer `python app.py`, `production`, `APP_HOST`, et la voie
    recommandée `WSGI` — ces marqueurs sont verrouillés par
    `tests/test_app_py_prod_host_guard_001.py` pour que toute reformulation
    future conserve l'information actionnable.
    """
    return (
        f"Refus de démarrer `python app.py` en production sur une interface publique.\n"
        f"\n"
        f"  APP_ENV  = {app_env!r}\n"
        f"  APP_HOST = {app_host!r}\n"
        f"\n"
        f"`python app.py` est un serveur de développement — il ne doit pas\n"
        f"être exposé publiquement en production.\n"
        f"\n"
        f"Pour la production publique, utiliser WSGI + Gunicorn + reverse proxy.\n"
        f"Voir docs/deployment/wsgi-deployment.md.\n"
        f"\n"
        f"Pour rester sur `python app.py` en mode prod local, limiter APP_HOST à\n"
        f"127.0.0.1, localhost ou ::1.\n"
        f"\n"
        f"Aucun serveur Forge n'a été démarré."
    )


def should_block_prod_public_host(app_env: str, app_host: str) -> bool:
    """True si la combinaison (env, host) doit déclencher le garde.

    Le garde se déclenche **uniquement** quand `APP_ENV` normalise à `"prod"`
    ET que `APP_HOST` est un hôte public dangereux. Tous les autres
    environnements (dev, test, staging, …) sont laissés intacts.
    """
    return (
        (app_env or "").strip().lower() == "prod"
        and is_dangerous_public_host(app_host)
    )


def format_port_in_use_message(host: str, port: int) -> str:
    """
    Message lisible quand le bind échoue avec EADDRINUSE.

    Ne suggère pas de tuer le processus existant : ce ticket ne fait pas de
    gestion automatique de processus.
    """
    return (
        f"Impossible de démarrer Forge.\n"
        f"\n"
        f"Le port {port} est déjà utilisé sur {host}.\n"
        f"\n"
        f"Un serveur Forge est peut-être déjà lancé, ou un autre processus "
        f"utilise ce port.\n"
        f"\n"
        f"Commandes utiles :\n"
        f"  ss -tulpn | grep :{port}\n"
        f"  lsof -i :{port}\n"
        f"\n"
        f"Solutions possibles :\n"
        f"  - arrêter l'ancien processus ;\n"
        f"  - changer APP_PORT dans env/dev ;\n"
        f"  - relancer python app.py.\n"
        f"\n"
        f"Aucun serveur Forge n'a été démarré."
    )
