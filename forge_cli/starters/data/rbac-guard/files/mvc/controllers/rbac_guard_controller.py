"""Starter Protéger une route — palier 2 du niveau intermédiaire (welcome-rbac).

Ticket : STARTER-RBAC-GUARD-001.

``require_contract_permission`` est la **garde de route** : elle renvoie une réponse
``403`` si les rôles n'accordent pas la permission requise, sinon ``None`` (la route
continue). Une ligne en tête de contrôleur suffit à protéger une action.

  ``index`` — `GET /rbac-guard?roles=...` : la « ressource protégée » exige
              ``article.create`` ; refusée (403) sinon.

Garde **déclarative**, aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import load_rbac_contract, require_contract_permission

_REQUIRED = "article.create"


class RbacGuardController(BaseController):
    """Starter pédagogique : protéger une route par une permission contractuelle."""

    @staticmethod
    def index(request: Request) -> Response:
        roles_raw = request.query("roles") or "reader"
        roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
        result = load_rbac_contract(".")
        context = {"roles": roles_raw, "required": _REQUIRED}
        denied = require_contract_permission(result, roles, _REQUIRED)
        if denied is not None:
            context["denied"] = True
            return BaseController.render("rbac_guard/index.html", context=context, request=request, status=403)
        context["allowed"] = True
        return BaseController.render("rbac_guard/index.html", context=context, request=request)
