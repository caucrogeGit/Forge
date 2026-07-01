# pyright: strict
"""forge-mvc-admin — Opt-in de back-office applicatif Forge.

Couche châssis (couche 1 de l'architecture hybride, voir la roadmap de cadrage
section 7) : ce paquet porte le contrat d'une ressource administrable
(`AdminResource`) et le registre explicite (`AdminRegistry`) que les vues
consommeront. Les vues, les actions et la sécurité HTTP viendront par les
tickets `ADMIN-*` suivants.

Voir `docs/roadmap/forge-admin-roadmap.md`.
"""
from forge_mvc_admin.exceptions import (
    AdminError,
    AdminRegistryError,
    AdminResourceError,
)
from forge_mvc_admin.http import AdminController, register_admin_routes
from forge_mvc_admin.registry import AdminRegistry, registry
from forge_mvc_admin.resources import AdminResource

__version__ = "1.0.0rc2"

__all__ = [
    "AdminResource",
    "AdminRegistry",
    "registry",
    "AdminController",
    "register_admin_routes",
    "AdminError",
    "AdminResourceError",
    "AdminRegistryError",
]

# Enregistre les templates embarqués (templates/admin/…) auprès du cœur (ADR-046),
# de sorte que `render("admin/…")` les résolve. Dégradation gracieuse si le cœur
# ou jinja2 ne sont pas présents (ex. analyse statique du paquet hors runtime).
try:
    from jinja2 import PackageLoader as _PackageLoader

    from core.mvc.controller.registry import (
        register_jinja_template_loader as _register_loader,
    )

    _register_loader(_PackageLoader("forge_mvc_admin", "templates"))
except ImportError:
    pass
