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
from core.mvc.view.pagination import Pagination
from core.security.decorators import require_auth

from forge_mvc_admin.exceptions import AdminRegistryError
from forge_mvc_admin.query import (
    FetchAll,
    FetchOne,
    Insert,
    count_rows,
    detail_columns,
    get_row,
    insert_row,
    list_rows,
)
from forge_mvc_admin.registry import AdminRegistry
from forge_mvc_admin.registry import registry as _default_registry

if TYPE_CHECKING:
    from core.http.request import Request
    from core.http.response import Response

__all__ = ["AdminController", "register_admin_routes"]

# Nombre de lignes par page de liste.
_PAGE_SIZE = 20


class AdminController:
    """Contrôleur du back-office. Détient le registre des ressources à afficher.

    Les accès base sont injectables (`fetch_all` / `fetch_one`) pour les tests ;
    par défaut, ils sont résolus paresseusement vers `core.database.db` afin que
    l'import du paquet ne tire pas la couche base de données.
    """

    def __init__(
        self,
        registry: AdminRegistry,
        *,
        fetch_all: FetchAll | None = None,
        fetch_one: FetchOne | None = None,
        insert: Insert | None = None,
    ) -> None:
        self._registry = registry
        self._fetch_all = fetch_all
        self._fetch_one = fetch_one
        self._insert = insert

    def _db(self) -> tuple[FetchAll, FetchOne]:
        fetch_all, fetch_one = self._fetch_all, self._fetch_one
        if fetch_all is None or fetch_one is None:
            from core.database.db import fetch_all as _fa, fetch_one as _fo
            fetch_all = fetch_all or _fa
            fetch_one = fetch_one or _fo
        return fetch_all, fetch_one

    def _insert_fn(self) -> Insert:
        if self._insert is not None:
            return self._insert
        from core.database.db import insert as _insert
        return _insert

    def dashboard(self, request: Request) -> Response:
        """Tableau de bord : liste les ressources administrables déclarées."""
        return BaseController.render(
            "admin/dashboard.html",
            context={"resources": self._registry.all()},
            request=request,
        )

    def resource_list(self, request: Request) -> Response:
        """Liste paginée des lignes d'une ressource (`GET /admin/<slug>`)."""
        slug = request.route("slug")
        if slug is None:
            return BaseController.not_found()
        try:
            resource = self._registry.get(slug)
        except AdminRegistryError:
            return BaseController.not_found()

        fetch_all, fetch_one = self._db()
        total = count_rows(resource, fetch_one)
        pagination = Pagination(request, total, _PAGE_SIZE)
        rows = list_rows(resource, fetch_all, limit=pagination.limit, offset=pagination.offset)
        return BaseController.render(
            "admin/list.html",
            context={
                "resource": resource,
                "columns": resource.list_fields,
                "rows": rows,
                "pagination": pagination.to_dict(),
            },
            request=request,
        )

    def resource_detail(self, request: Request) -> Response:
        """Fiche d'une ligne d'une ressource (`GET /admin/<slug>/<id>`)."""
        slug = request.route("slug")
        pk_value = request.route("id")
        if slug is None or pk_value is None:
            return BaseController.not_found()
        try:
            resource = self._registry.get(slug)
        except AdminRegistryError:
            return BaseController.not_found()

        _fetch_all, fetch_one = self._db()
        row = get_row(resource, fetch_one, pk_value=pk_value)
        if row is None:
            return BaseController.not_found()
        return BaseController.render(
            "admin/detail.html",
            context={
                "resource": resource,
                "columns": detail_columns(resource),
                "row": row,
            },
            request=request,
        )

    def resource_new(self, request: Request) -> Response:
        """Formulaire de création vide (`GET /admin/<slug>/new`)."""
        slug = request.route("slug")
        if slug is None:
            return BaseController.not_found()
        try:
            resource = self._registry.get(slug)
        except AdminRegistryError:
            return BaseController.not_found()
        return BaseController.render(
            "admin/form.html",
            context={
                "resource": resource,
                "fields": resource.form_fields,
                "action": f"/admin/{resource.slug}/new",
                "values": {field: "" for field in resource.form_fields},
                "error": "",
                "title": f"Nouveau : {resource.label}",
            },
            request=request,
        )

    def resource_create(self, request: Request) -> Response:
        """Création d'une ligne (`POST /admin/<slug>/new`).

        Seules les colonnes `form_fields` sont écrites (liste blanche, valeurs
        paramétrées). Une valeur vide devient `NULL`. CSRF vérifié en amont par
        le middleware. En cas de succès, redirection vers la fiche créée.
        """
        slug = request.route("slug")
        if slug is None:
            return BaseController.not_found()
        try:
            resource = self._registry.get(slug)
        except AdminRegistryError:
            return BaseController.not_found()

        posted = BaseController.body(request)
        params: list[str | None] = [
            (value.strip() or None)
            for value in (posted.get(field, "") for field in resource.form_fields)
        ]
        new_id = insert_row(resource, self._insert_fn(), values=params)
        return BaseController.redirect_with_flash(
            request,
            f"/admin/{resource.slug}/{new_id}",
            f"{resource.label} créé.",
        )


def register_admin_routes(router: Any, *, registry: AdminRegistry | None = None) -> None:
    """Branche les routes du back-office sur un Router Forge.

    Appelée explicitement par l'application (ADR-030, principe 9). Sans argument
    `registry`, utilise le registre par défaut du processus.

    Les routes ne sont pas publiques : l'utilisateur doit être authentifié
    (sinon redirection vers /login).
    """
    controller = AdminController(registry if registry is not None else _default_registry)
    router.add(
        "GET",
        "/admin",
        require_auth(controller.dashboard),
        name="admin-dashboard",
    )
    router.add(
        "GET",
        "/admin/{slug}",
        require_auth(controller.resource_list),
        name="admin-resource-list",
    )
    # `/new` (littéral) doit être enregistré AVANT `/{id}` : le routeur retient la
    # première route qui matche, sinon GET /admin/<slug>/new prendrait id="new".
    router.add(
        "GET",
        "/admin/{slug}/new",
        require_auth(controller.resource_new),
        name="admin-resource-new",
    )
    router.add(
        "POST",
        "/admin/{slug}/new",
        require_auth(controller.resource_create),
        name="admin-resource-create",
    )
    router.add(
        "GET",
        "/admin/{slug}/{id}",
        require_auth(controller.resource_detail),
        name="admin-resource-detail",
    )
