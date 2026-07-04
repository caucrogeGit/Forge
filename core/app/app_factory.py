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
    # `config` est le module de l'APPLICATION (présent dans un projet généré,
    # absent du dépôt framework). Chargé dynamiquement et typé `Any` : l'analyse
    # statique du framework ne peut pas le résoudre, et ce n'est pas son rôle.
    config: Any = importlib.import_module("config")
    # ADR-060 : la config de connexion BDD n'est plus poussée dans le cœur ; le
    # backend installé la lit dans l'environnement (DB_APP_*, DB_NAME, …).
    kwargs = dict(
        app_name=config.APP_NAME, app_env=config.APP_ENV,
        views_dir=config.VIEWS_DIR, sql_dir=config.SQL_DIR,
        upload_max_size=config.UPLOAD_MAX_SIZE,
        trusted_proxies=config.APP_TRUSTED_PROXIES,
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
    config: Any = importlib.import_module("config")  # module applicatif (cf. _forge_config_kwargs)

    apply_forge_config()
    if template_manager._renderer is None:  # pyright: ignore[reportPrivateUsage]  # check d'idempotence du branchement renderer
        template_manager.register(Jinja2Renderer(config.VIEWS_DIR))
    routes_mod = importlib.import_module(config.APP_ROUTES_MODULE)
    forge.configure(router=routes_mod.router)
    return Application(routes_mod.router)
