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
from typing import TYPE_CHECKING, Any, cast

from core.mvc.controller.base_controller import BaseController
from core.mvc.view.pagination import Pagination
from core.security.decorators import require_auth

from forge_mvc_admin.exceptions import AdminRegistryError, AdminResourceError
from forge_mvc_admin.resources import AdminResource
from forge_mvc_admin.query import (
    BulkActionError,
    Execute,
    FetchAll,
    FetchOne,
    Insert,
    count_rows,
    delete_row,
    delete_rows,
    detail_columns,
    get_row,
    insert_row,
    list_rows,
    rows_by_pk,
    transition_rows,
    update_row,
)
from forge_mvc_admin.registry import AdminRegistry
from forge_mvc_admin.sessions_panel import sessions_panel
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

    def sessions(self, request: Request) -> Response:
        """Panneau des sessions actives (`GET /admin/_sessions`).

        Le chemin porte un tiret bas de tête : `/admin/{slug}` capturerait
        sinon `sessions` comme une ressource, et une application qui déclare
        une ressource nommée « sessions » prendrait la place de ce panneau.
        """
        return BaseController.render(
            "admin/sessions.html",
            context={"panel": sessions_panel()},
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

    # ── Actions groupées (ADMIN-BULK-ACTIONS-001) ───────────────────────────

    def _selection(self, request: Request) -> "list[str]":
        """Identifiants cochés dans la liste.

        Lus par `files_list`-like : le formulaire pose plusieurs champs du même
        nom, et n'en lire qu'un supprimerait une ligne sur N sans le dire.
        """
        lecteur = getattr(request, "body", None)
        if not isinstance(lecteur, dict):
            return []
        brut = cast("dict[str, Any]", lecteur).get("ids")
        if isinstance(brut, list):
            valeurs = cast("list[Any]", brut)
            return [str(v).strip() for v in valeurs if str(v).strip()]
        if brut:
            return [str(brut).strip()]
        return []

    def _resource_ou_404(self, request: Request) -> "AdminResource | None":
        slug = request.route("slug")
        if slug is None:
            return None
        try:
            return self._registry.get(slug)
        except AdminRegistryError:
            return None

    def resource_bulk_confirm(self, request: Request) -> Response:
        """Confirmation d'une action groupée (`POST /admin/<slug>/bulk`).

        En POST et non en GET : la sélection est longue, et une URL de plusieurs
        centaines d'identifiants serait tronquée par le serveur avant d'arriver.

        Ne mute **rien**. La suppression unitaire a sa page de confirmation ;
        une action qui porte sur cinquante lignes n'a pas moins besoin de la
        sienne.
        """
        from core.http.response import Response as _Response

        resource = self._resource_ou_404(request)
        if resource is None:
            return BaseController.not_found()

        action = str(request.form("action") or "").strip()
        identifiants = self._selection(request)
        if not identifiants:
            return BaseController.redirect_with_flash(
                request, f"/admin/{resource.slug}",
                "Aucune ligne sélectionnée.",
            )

        if action == "delete" and not resource.bulk_delete:
            return _Response.text(
                f"{resource.slug} n'ouvre pas la suppression groupée.", status=403
            )
        transition: "tuple[str, str] | None" = None
        if action.startswith("transition:"):
            transition = _parse_transition(resource, action)
            if transition is None:
                return _Response.text("Transition inconnue.", status=400)

        fetch_all, _fetch_one = self._db()
        lignes = rows_by_pk(resource, fetch_all, pk_values=identifiants)
        return BaseController.render(
            "admin/bulk.html",
            context={
                "resource": resource,
                "columns": resource.list_fields,
                "rows": lignes,
                "ids": identifiants,
                "action": action,
                "transition": transition,
                "manquantes": len(identifiants) - len(lignes),
            },
            request=request,
        )

    def resource_bulk_delete(self, request: Request) -> Response:
        """Suppression groupée (`POST /admin/<slug>/bulk-delete`)."""
        from core.http.response import Response as _Response

        resource = self._resource_ou_404(request)
        if resource is None:
            return BaseController.not_found()
        if not resource.bulk_delete:
            return _Response.text(
                f"{resource.slug} n'ouvre pas la suppression groupée.", status=403
            )

        try:
            supprimees = delete_rows(
                resource, self._execute_fn(), pk_values=self._selection(request)
            )
        except BulkActionError as erreur:
            return _Response.text(str(erreur), status=400)

        return BaseController.redirect_with_flash(
            request, f"/admin/{resource.slug}",
            f"{supprimees} {resource.plural_label.lower()} supprimés.",
        )

    def resource_bulk_transition(self, request: Request) -> Response:
        """Transition groupée (`POST /admin/<slug>/bulk-transition`).

        Exige `forge-mvc-workflow` **installé**, et refuse sinon.

        Ce refus est délibéré, et il diffère de la suppression : appliquer un
        changement de statut à N lignes sans pouvoir vérifier que la transition
        est déclarée écrirait un état que le workflow de l'application interdit
        peut-être, sur cinquante lignes d'un coup. Une fonctionnalité absente
        vaut mieux qu'une fonctionnalité qui contourne la règle.
        """
        from core.http.response import Response as _Response

        resource = self._resource_ou_404(request)
        if resource is None:
            return BaseController.not_found()

        transition = _parse_transition(
            resource, str(request.form("action") or "").strip()
        )
        if transition is None:
            return _Response.text("Transition inconnue.", status=400)

        refus = _verifier_transition_workflow(resource, transition)
        if refus is not None:
            return _Response.text(refus, status=409)

        depuis, vers = transition
        try:
            passees = transition_rows(
                resource, self._execute_fn(),
                pk_values=self._selection(request),
                from_status=depuis, to_status=vers,
            )
        except BulkActionError as erreur:
            return _Response.text(str(erreur), status=400)

        demandees = len(self._selection(request))
        message = f"{passees} {resource.plural_label.lower()} passés en « {vers} »."
        if passees < demandees:
            # L'écart est une information : une ligne dont le statut a changé
            # entre l'affichage et la validation n'a pas été touchée, et le
            # taire ferait croire l'action complète.
            message += (
                f" {demandees - passees} n'étaient plus en « {depuis} » et "
                "n'ont pas été touchés."
            )
        return BaseController.redirect_with_flash(
            request, f"/admin/{resource.slug}", message
        )


def _parse_transition(
    resource: "AdminResource", action: str
) -> "tuple[str, str] | None":
    """Transition désignée par `transition:<depuis>:<vers>`, si elle est déclarée.

    La comparaison porte sur les transitions **déclarées par la ressource** :
    une valeur venue du formulaire ne peut donc désigner qu'un couple que
    l'application a écrit.
    """
    if not action.startswith("transition:"):
        return None
    morceaux = action.split(":", 2)
    if len(morceaux) != 3:
        return None
    couple = (morceaux[1], morceaux[2])
    return couple if couple in resource.bulk_transitions else None


def _verifier_transition_workflow(
    resource: "AdminResource", transition: "tuple[str, str]"
) -> "str | None":
    """Refus motivé, ou `None` si la transition est jouable.

    `forge-mvc-workflow` est importé paresseusement, comme `forge-mvc-rbac`
    l'est pour la garde de permission : `forge-mvc-admin` ne le déclare pas en
    dépendance, et un projet qui n'a pas de workflow n'a pas à l'installer pour
    afficher une liste.
    """
    depuis, vers = transition
    try:
        from forge_mvc_workflow import (  # type: ignore[import-not-found]
            can_transition,
            ensure_conditions,
            make_transition,
        )
    except ImportError:
        return (
            "La transition groupée exige l'opt-in forge-mvc-workflow "
            "(pip install forge-mvc-workflow). Sans lui, rien ne peut vérifier "
            "que la transition est déclarée, et l'appliquer à plusieurs lignes "
            "écrirait un état que le workflow interdit peut-être."
        )

    declarees = [make_transition(d, v) for d, v in resource.bulk_transitions]
    if not can_transition(declarees, depuis, vers):
        return f"Transition non déclarée : « {depuis} » vers « {vers} »."
    try:
        ensure_conditions(depuis, vers, {"resource": resource.slug, "bulk": True})
    except Exception as exc:  # noqa: BLE001 — le motif remonte à l'écran
        return str(exc)
    return None


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
    les routes admin exigent cette permission via `forge-mvc-rbac`.

    Sans `forge-mvc-rbac` installé, une route portant une permission déclarée
    répond **403**. C'est un comportement **fail-closed** : on ne peut pas
    vérifier la permission, donc on refuse. Ce paragraphe écrivait « fail-open »
    alors que le code refusait, contradiction relevée en revue : une
    documentation qui annonce une ouverture là où le code ferme fait chercher
    une faille qui n'existe pas, et inversement.

    Par défaut, aucune permission n'est exigée : auth seule.
    """
    controller = AdminController(registry if registry is not None else _default_registry)

    def protect(handler: Handler) -> Handler:
        # auth d'abord (redirige /login), puis permission RBAC optionnelle (403).
        return require_auth(_permission_guard(handler, permission))

    router.add("GET", "/admin", protect(controller.dashboard), name="admin-dashboard")
    # Avant `/admin/{slug}` : le routeur retient la première route qui
    # matche, et `_sessions` serait sinon lu comme un slug de ressource.
    router.add(
        "GET", "/admin/_sessions", protect(controller.sessions),
        name="admin-sessions",
    )
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
    # Actions groupées (ADMIN-BULK-ACTIONS-001). Toutes en POST : la sélection
    # est longue, et une URL de plusieurs centaines d'identifiants serait
    # tronquée avant d'arriver. Le CSRF s'applique donc, par défaut du routeur.
    #
    # Déclarées APRÈS `/{id}/delete` : `/admin/{slug}/bulk` ne peut pas être
    # confondu avec `/admin/{slug}/{id}`, les deux segments diffèrent, mais
    # l'ordre reste explicite pour qui relit.
    router.add(
        "POST",
        "/admin/{slug}/bulk",
        protect(controller.resource_bulk_confirm),
        name="admin-resource-bulk-confirm",
    )
    router.add(
        "POST",
        "/admin/{slug}/bulk-delete",
        protect(controller.resource_bulk_delete),
        name="admin-resource-bulk-delete",
    )
    router.add(
        "POST",
        "/admin/{slug}/bulk-transition",
        protect(controller.resource_bulk_transition),
        name="admin-resource-bulk-transition",
    )
