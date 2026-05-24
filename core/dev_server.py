"""
core/dev_server.py — Messages de diagnostic du serveur de développement
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
