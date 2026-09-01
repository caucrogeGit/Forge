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

import logging
from urllib.parse import urlencode
from typing import TYPE_CHECKING, Any

from core.mvc.controller.base_controller import BaseController
from core.mvc.view.pagination import Pagination
from core.security.decorators import require_auth

from forge_mvc_admin.exceptions import AdminRegistryError, AdminResourceError
from forge_mvc_admin.query import (
    Execute,
    FetchAll,
    FetchOne,
    Insert,
    count_rows,
    delete_row,
    detail_columns,
    get_row,
    insert_row,
    list_rows,
    update_row,
)
from forge_mvc_admin.registry import AdminRegistry
from forge_mvc_admin.registry import registry as _default_registry

if TYPE_CHECKING:
    from core.http.request import Request
    from core.http.response import Response
    from core.http.router import Handler

logger = logging.getLogger(__name__)

__all__ = ["AdminController", "register_admin_routes"]

# Nombre de lignes par page de liste.
_PAGE_SIZE = 20


def _criteria_query(
    filters: "dict[str, str]",
    search: "str | None",
    sort: "str | None",
    descending: bool,
) -> str:
    """Critères courants en chaîne de requête, `page` exclue.

    Rend une chaîne vide quand rien n'est demandé, et commence par `&` sinon :
    elle se colle derrière un `?page=N` déjà présent. L'encodage passe par
    `urlencode`, un terme de recherche pouvant contenir `&` ou `=`.
    """
    couples: list[tuple[str, str]] = sorted(filters.items())
    if search:
        couples.append(("q", search))
    if sort:
        couples.append(("tri", sort))
    if descending:
        couples.append(("sens", "desc"))
    return ("&" + urlencode(couples)) if couples else ""


def _permission_guard(handler: Handler, permission: str | None) -> Handler:
    """Garde de permission RBAC **optionnelle** (ADMIN-RBAC-INTEGRATION-001).

    Si `permission` est `None`, le handler est renvoyé tel quel (auth seule).
    Sinon, la permission est vérifiée via `forge-mvc-rbac` **s'il est installé** :
    refus en 403 quand elle manque. Si `forge-mvc-rbac` est absent alors qu'une
    permission est déclarée, la garde REFUSE (fail-closed, 403 + log) : on ne peut
    pas vérifier la permission, donc on sécurise par défaut. Sans permission
    déclarée (`None`), l'admin reste accessible (auth seule) — pas de dépendance dure.
    """
    if permission is None:
        return handler

    def guarded(request: Request) -> Response:
        try:
            from forge_mvc_rbac import require_contract_permission_for_request
        except ImportError:
            # Fail-closed (ADMIN-RBAC-FAILCLOSED-001) : permission déclarée mais
            # forge-mvc-rbac absent. On ne peut pas la vérifier -> refus (403),
            # sécuriser par défaut (charte principe 7), plutôt que de laisser
            # passer silencieusement.
            from core.http.response import Response

            logger.warning(
                "Route admin protégée par la permission %r mais forge-mvc-rbac "
                "n'est pas installé : accès refusé (403). Installez forge-mvc-rbac.",
                permission,
            )
            return Response.text(
                "Accès refusé : cette route requiert une permission mais "
                "forge-mvc-rbac n'est pas installé.",
                status=403,
            )
        denied = require_contract_permission_for_request(request, permission)
        if denied is not None:
            return denied
        return handler(request)

    return guarded


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
        execute: Execute | None = None,
    ) -> None:
        self._registry = registry
        self._fetch_all = fetch_all
        self._fetch_one = fetch_one
        self._insert = insert
        self._execute = execute

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

    def _execute_fn(self) -> Execute:
        if self._execute is not None:
            return self._execute
        from core.database.db import execute as _execute
        return _execute

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

        # Les critères viennent de l'URL : `query.py` les vérifie contre les
        # champs déclarés par la ressource, et refuse tout le reste. Une
        # demande invalide rend 400 plutôt que 500 : elle est fautive, pas
        # cassée (ADMIN-LIST-FILTERS-001).
        filters = {
            champ: valeur
            for champ in resource.filter_fields
            if (valeur := request.query(champ)) not in (None, "")
        }
        search = request.query("q")
        sort = request.query("tri")
        descending = request.query("sens") == "desc"

        fetch_all, fetch_one = self._db()
        try:
            total = count_rows(resource, fetch_one, filters=filters, search=search)
            pagination = Pagination(request, total, _PAGE_SIZE)
            rows = list_rows(
                resource, fetch_all,
                limit=pagination.limit, offset=pagination.offset,
                filters=filters, search=search, sort=sort, descending=descending,
            )
        except AdminResourceError as erreur:
            # Import local : `Response` n'est importée qu'en TYPE_CHECKING en
            # tête de module, motif déjà suivi par la garde de permission.
            from core.http.response import Response

            return Response.text(str(erreur), status=400)

        return BaseController.render(
            "admin/list.html",
            context={
                "resource": resource,
                "columns": resource.list_fields,
                "rows": rows,
                "pagination": pagination.to_dict(),
                "filters": filters,
                "search": search or "",
                "sort": sort or "",
                "descending": descending,
                # Les critères suivent la pagination : sans cela, tourner une
                # page les perdrait, et la liste repartirait entière.
                "criteria_query": _criteria_query(filters, search, sort, descending),
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

    def resource_edit(self, request: Request) -> Response:
        """Formulaire d'édition pré-rempli (`GET /admin/<slug>/<id>/edit`)."""
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
        values = {
            field: ("" if row.get(field) is None else row[field])
            for field in resource.form_fields
        }
        return BaseController.render(
            "admin/form.html",
            context={
                "resource": resource,
                "fields": resource.form_fields,
                "action": f"/admin/{resource.slug}/{pk_value}/edit",
                "values": values,
                "error": "",
                "title": f"Modifier : {resource.label}",
            },
            request=request,
        )

    def resource_update(self, request: Request) -> Response:
        """Mise à jour d'une ligne (`POST /admin/<slug>/<id>/edit`).

        Mêmes garanties que la création : colonnes `form_fields` en liste
        blanche, valeurs paramétrées, CSRF vérifié en amont. Succès → fiche.
        """
        slug = request.route("slug")
        pk_value = request.route("id")
        if slug is None or pk_value is None:
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
        update_row(resource, self._execute_fn(), values=params, pk_value=pk_value)
        return BaseController.redirect_with_flash(
            request,
            f"/admin/{resource.slug}/{pk_value}",
            f"{resource.label} modifié.",
        )

    def resource_confirm_delete(self, request: Request) -> Response:
        """Page de confirmation de suppression (`GET /admin/<slug>/<id>/delete`).

        En lecture seule : ne supprime rien, affiche la ligne et un formulaire
        POST. La suppression effective passe par `resource_delete`.
        """
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
            "admin/delete.html",
            context={
                "resource": resource,
                "columns": detail_columns(resource),
                "row": row,
                "action": f"/admin/{resource.slug}/{pk_value}/delete",
            },
            request=request,
        )

    def resource_delete(self, request: Request) -> Response:
        """Suppression d'une ligne (`POST /admin/<slug>/<id>/delete`).

        Action de mutation : toujours en POST, CSRF vérifié en amont. Succès →
        redirection vers la liste avec flash.
        """
        slug = request.route("slug")
        pk_value = request.route("id")
        if slug is None or pk_value is None:
            return BaseController.not_found()
        try:
            resource = self._registry.get(slug)
        except AdminRegistryError:
            return BaseController.not_found()

        delete_row(resource, self._execute_fn(), pk_value=pk_value)
        return BaseController.redirect_with_flash(
            request,
            f"/admin/{resource.slug}",
            f"{resource.label} supprimé.",
        )


def register_admin_routes(
    router: Any,
    *,
    registry: AdminRegistry | None = None,
    permission: str | None = None,
) -> None:
    """Branche les routes du back-office sur un Router Forge.

    Appelée explicitement par l'application (ADR-030, principe 9). Sans argument
    `registry`, utilise le registre par défaut du processus.

    Les routes ne sont pas publiques : l'utilisateur doit être authentifié
    (sinon redirection vers /login).

    `permission` (opt-in RBAC, ADMIN-RBAC-INTEGRATION-001) : si fournie, toutes
    les routes admin exigent cette permission via `forge-mvc-rbac` **s'il est
    installé** (403 sinon). Sans `forge-mvc-rbac`, une route avec permission déclarée renvoie 403 (auth
    seule, fail-open ; `forge doctor` avertit). Par défaut, aucune permission
    n'est exigée : auth seule.
    """
    controller = AdminController(registry if registry is not None else _default_registry)

    def protect(handler: Handler) -> Handler:
        # auth d'abord (redirige /login), puis permission RBAC optionnelle (403).
        return require_auth(_permission_guard(handler, permission))

    router.add("GET", "/admin", protect(controller.dashboard), name="admin-dashboard")
    router.add(
        "GET",
        "/admin/{slug}",
        protect(controller.resource_list),
        name="admin-resource-list",
    )
    # `/new` (littéral) doit être enregistré AVANT `/{id}` : le routeur retient la
    # première route qui matche, sinon GET /admin/<slug>/new prendrait id="new".
    router.add(
        "GET",
        "/admin/{slug}/new",
        protect(controller.resource_new),
        name="admin-resource-new",
    )
    router.add(
        "POST",
        "/admin/{slug}/new",
        protect(controller.resource_create),
        name="admin-resource-create",
    )
    router.add(
        "GET",
        "/admin/{slug}/{id}",
        protect(controller.resource_detail),
        name="admin-resource-detail",
    )
    router.add(
        "GET",
        "/admin/{slug}/{id}/edit",
        protect(controller.resource_edit),
        name="admin-resource-edit",
    )
    router.add(
        "POST",
        "/admin/{slug}/{id}/edit",
        protect(controller.resource_update),
        name="admin-resource-update",
    )
    router.add(
        "GET",
        "/admin/{slug}/{id}/delete",
        protect(controller.resource_confirm_delete),
        name="admin-resource-delete-confirm",
    )
    router.add(
        "POST",
        "/admin/{slug}/{id}/delete",
        protect(controller.resource_delete),
        name="admin-resource-delete",
    )
