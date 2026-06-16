# pyright: strict
"""core/app/app_factory.py — Construction de l'`Application` Forge configurée.

Ticket : WSGI-APP-FACTORY-CONFIG-001.

Source unique d'initialisation : lit `config.py`, applique
`forge.configure(...)`, branche le renderer Jinja2, charge les routes et
construit l'`Application`. Réutilisée par les points d'entrée serveur de
développement (`app.py`) et WSGI (`core.app.wsgi.create_configured_wsgi_app`)
pour qu'aucune divergence de configuration ne s'installe entre les deux.

Les fonctions sont idempotentes : un second appel reconfigure Forge sans
casser l'état précédent (`forge.configure(**kwargs)` réécrit les clés
existantes, et le renderer Jinja2 n'est branché que si aucun renderer
n'est déjà enregistré).
"""
from __future__ import annotations

import importlib
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from core.app.application import Application


def _forge_config_kwargs() -> dict[str, Any]:
    """Lit `config.py` et retourne les kwargs à passer à `forge.configure(...)`.

    Réplique fidèlement le `forge.configure(...)` central de `app.py` —
    toute évolution doit être miroitée des deux côtés (couverte par
    `tests/test_wsgi_app_factory_config_001.py::TestConfigParity`).
    """
    from config import (
        APP_NAME, APP_ENV, VIEWS_DIR, SQL_DIR,
        UPLOAD_MAX_SIZE,
        DB_APP_HOST, DB_APP_PORT, DB_NAME, DB_APP_LOGIN, DB_APP_PWD,
        DB_POOL_SIZE,
        APP_TRUSTED_PROXIES,
    )
    kwargs = dict(
        app_name=APP_NAME, app_env=APP_ENV,
        views_dir=VIEWS_DIR, sql_dir=SQL_DIR,
        upload_max_size=UPLOAD_MAX_SIZE,
        db_host=DB_APP_HOST, db_port=DB_APP_PORT, db_name=DB_NAME,
        db_user=DB_APP_LOGIN, db_password=DB_APP_PWD,
        db_pool_size=DB_POOL_SIZE,
        trusted_proxies=APP_TRUSTED_PROXIES,
    )
    return kwargs


def apply_forge_config() -> None:
    """Applique la configuration Forge depuis `config.py`. Idempotent."""
    import core.forge as forge
    forge.configure(**_forge_config_kwargs())


def build_application() -> "Application":
    """Construit l'`Application` Forge complète : config + Jinja + routes.

    Exécute la même séquence d'initialisation que `app.py`, sans démarrer
    le serveur HTTP. Retourne une `core.app.application.Application` prête à
    dispatcher.
    """
    import core.forge as forge
    from core.app.application import Application
    from core.templating.manager import template_manager
    from integrations.jinja2.renderer import Jinja2Renderer
    from config import APP_ROUTES_MODULE, VIEWS_DIR

    apply_forge_config()
    if template_manager._renderer is None:  # pyright: ignore[reportPrivateUsage]  # check d'idempotence du branchement renderer
        template_manager.register(Jinja2Renderer(VIEWS_DIR))
    routes_mod = importlib.import_module(APP_ROUTES_MODULE)
    forge.configure(router=routes_mod.router)
    return Application(routes_mod.router)
