# pyright: strict
"""Intégration HTTP de Forge Admin (ADMIN-DASHBOARD-MINIMAL-001).

Expose `register_admin_routes(router)` — branchement explicite par l'application
(ADR-030) — et `AdminController`, dont le dashboard liste les ressources
enregistrées dans le registre.

Sécurité : la route `/admin` n'est pas publique, donc l'``AuthMiddleware`` par
défaut de l'application l'exige déjà ; le handler est en plus protégé par
`@require_auth` (défense en profondeur, charte principe 7), si bien que le
back-office reste fermé même si l'application a personnalisé sa chaîne de
middlewares.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from core.mvc.controller.base_controller import BaseController
from core.security.decorators import require_auth

from forge_mvc_admin.registry import AdminRegistry
from forge_mvc_admin.registry import registry as _default_registry

if TYPE_CHECKING:
    from core.http.request import Request
    from core.http.response import Response

__all__ = ["AdminController", "register_admin_routes"]


class AdminController:
    """Contrôleur du back-office. Détient le registre des ressources à afficher."""

    def __init__(self, registry: AdminRegistry) -> None:
        self._registry = registry

    def dashboard(self, request: Request) -> Response:
        """Tableau de bord : liste les ressources administrables déclarées."""
        return BaseController.render(
            "admin/dashboard.html",
            context={"resources": self._registry.all()},
            request=request,
        )


def register_admin_routes(router: Any, *, registry: AdminRegistry | None = None) -> None:
    """Branche les routes du back-office sur un Router Forge.

    Appelée explicitement par l'application (ADR-030, principe 9). Sans argument
    `registry`, utilise le registre par défaut du processus.

    La route du dashboard n'est pas publique : l'utilisateur doit être
    authentifié (sinon redirection vers /login).
    """
    controller = AdminController(registry if registry is not None else _default_registry)
    router.add(
        "GET",
        "/admin",
        require_auth(controller.dashboard),
        name="admin-dashboard",
    )
