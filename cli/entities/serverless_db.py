# pyright: strict
"""Connexion runtime d'un backend BDD sans serveur (ex. SQLite, ADR-054).

db:init, db:apply et les migrations connectent un SGBD serveur (MariaDB) avec
les comptes d'administration (DB_ADMIN_*). Un backend sans serveur (SQLite) n'a
ni comptes ni base à provisionner : il suffit de configurer le cœur avec le
chemin du fichier (DB_NAME du projet), puis d'emprunter une connexion au
backend actif.

Cette étape de configuration est nécessaire car le contexte CLI ne passe pas
par forge.configure() (contrairement au runtime applicatif).
"""
from __future__ import annotations

from typing import Any


def configure_serverless_db() -> Any:
    """Configure core.forge depuis le config projet ; retourne ce config.

    À appeler avant ``get_backend().get_connection()`` dans une commande CLI.
    """
    import core.forge as forge
    from cli.project.project_config import load_project_config

    # load_project_config() charge l'environnement (load_dotenv) : le backend
    # sans serveur lit ensuite DB_NAME (chemin du fichier) dans os.environ (ADR-060).
    config = load_project_config()
    forge.configure(app_name=getattr(config, "APP_NAME", "forge"))
    return config
