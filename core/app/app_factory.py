# pyright: strict
"""core/app/app_factory.py — Construction de l'`Application` Forge configurée.

Ticket : WSGI-APP-FACTORY-CONFIG-001.

Lit `config.py`, applique `forge.configure(...)`, branche le renderer Jinja2,
charge les routes et construit l'`Application`.

Portée exacte, et elle est plus étroite que ce qui était écrit ici : cette
fabrique voit ce que `config.py` DÉCLARE, c'est à dire des valeurs. Les
middlewares et le magasin de sessions sont des objets, construits dans `app.py`
là où le squelette le prescrit, et elle ne peut pas les voir.

Elle n'est donc pas la source unique d'initialisation des deux points d'entrée.
Le croire a coûté une mise en production servie sans ses gardes (ADR-092) :
`core.app.wsgi.create_configured_wsgi_app` refuse désormais de construire quand
`app.py` câble ce que cette fabrique ignore.

Les fonctions sont idempotentes : un second appel reconfigure Forge sans
casser l'état précédent (`forge.configure(**kwargs)` réécrit les clés
existantes, et le renderer Jinja2 n'est branché que si aucun renderer
n'est déjà enregistré).
"""
from __future__ import annotations

import importlib
import importlib.util
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

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


def project_root() -> "Path | None":
    """Racine du projet applicatif, déduite de l'emplacement de `config.py`.

    `config.py` vit à la racine par contrat du squelette : son dossier EST la
    racine, ce que ni le répertoire courant ni `sys.path[0]` ne garantissent
    sous un serveur WSGI.

    Rend `None` quand la question n'a pas de réponse ici (pas de `config`
    importable, module sans fichier). Aucun appelant ne doit en faire une
    erreur : ce chemin sert à des vérifications qui se taisent quand elles ne
    peuvent pas conclure.
    """
    from pathlib import Path

    try:
        config: Any = importlib.import_module("config")
    except Exception:  # noqa: BLE001 — absence de config : rien à déduire
        return None
    fichier = getattr(config, "__file__", None)
    if not fichier:
        return None
    return Path(str(fichier)).resolve().parent


#: Module de câblage du projet, lu par les DEUX points d'entrée (ADR-093).
BOOTSTRAP_MODULE = "bootstrap"


def load_bootstrap() -> "Any | None":
    """Module de câblage du projet, ou `None` s'il n'en a pas.

    Ticket : `SKELETON-BOOTSTRAP-WIRING-001`. Décision : ADR-093.

    Le câblage (middlewares, magasin de sessions) vivait dans `app.py`, que
    cette fabrique ne lit pas : le chemin WSGI construisait donc une
    application privée de ses gardes (ADR-092). Il vit désormais dans un module
    que les deux points d'entrée lisent, ce qui rend la divergence impossible
    plutôt que détectable.

    Un projet sans `bootstrap.py` n'en a pas besoin : `None`, et le
    comportement d'avant s'applique. Forge n'écrit jamais dans un projet
    existant (principe 9), et il n'y a rien à migrer.

    **Une erreur DANS le module remonte.** La distinction est le tout du
    ticket : `find_spec` demande « ce module existe il ? », l'import demande
    « se charge t il ? ». Attraper l'ImportError de l'import ferait retomber un
    `bootstrap.py` cassé, un opt-in absent par exemple, sur une application
    silencieusement désarmée. C'est exactement le défaut que ce module corrige.
    """
    if importlib.util.find_spec(BOOTSTRAP_MODULE) is None:
        return None
    return importlib.import_module(BOOTSTRAP_MODULE)


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

    # ADR-093 : le câblage du projet, lu ici comme par `app.py`.
    # `configure_services` avant les middlewares : un middleware peut avoir
    # besoin d'un service, l'inverse ne se produit pas.
    bootstrap = load_bootstrap()
    middlewares: list[Any] | None = None
    if bootstrap is not None:
        configurer = getattr(bootstrap, "configure_services", None)
        if callable(configurer):
            configurer()
        construire = getattr(bootstrap, "build_middlewares", None)
        if callable(construire):
            # `bootstrap` est un module APPLICATIF : l'analyse statique du
            # framework ne peut pas le résoudre, et ce n'est pas son rôle (même
            # traitement que `config`). Le contrat est vérifié à l'exécution.
            produits: Any = construire()
            middlewares = list(produits)

    # `None` laisse le défaut d'`Application`, soit `[AuthMiddleware(...)]`.
    # Une liste VIDE est un choix explicite du projet, et retire jusqu'à
    # l'authentification : elle est transmise telle quelle.
    return Application(routes_mod.router, middlewares=middlewares)
