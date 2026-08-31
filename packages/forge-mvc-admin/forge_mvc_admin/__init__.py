# pyright: strict
"""forge-mvc-admin, opt-in de back-office applicatif Forge.

Ce paquet livre un back-office fonctionnel. Il porte le contrat d'une ressource
administrable (`AdminResource`), le registre explicite (`AdminRegistry`) et le
contrôleur HTTP (`AdminController`) qui sert le tableau de bord, la liste
paginée, le détail, la création, la modification et la suppression.

Les routes se branchent par `register_admin_routes(router)`, appel explicite de
l'application. Elles exigent une session authentifiée, et une permission RBAC
optionnelle vérifiée en refus par défaut quand `forge-mvc-rbac` est absent.

Ce qui reste à venir est suivi dans `docs/roadmap/forge-rc8-optins-roadmap.md`,
principalement les filtres de liste et les actions en masse.
"""
from forge_mvc_admin.exceptions import (
    AdminError,
    AdminRegistryError,
    AdminResourceError,
)
from forge_mvc_admin.http import AdminController, register_admin_routes
from forge_mvc_admin.registry import AdminRegistry, registry
from forge_mvc_admin.resources import AdminResource

__version__ = "1.0.0rc7"

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
