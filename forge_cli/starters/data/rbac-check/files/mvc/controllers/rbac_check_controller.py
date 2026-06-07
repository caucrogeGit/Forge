"""Starter Vérifier une permission — palier 1 du niveau intermédiaire (welcome-rbac).

Ticket : STARTER-RBAC-CHECK-001.

Le cœur du RBAC déclaratif : ``has_contract_permission`` répond « ce jeu de **rôles**
accorde-t-il cette **permission** selon le contrat ? ». Pur : il lit le contrat
``mvc/security/rbac.json`` (livré avec le starter), sans rien d'autre.

  ``index`` — `GET /rbac-check?roles=reader&permission=article.create` : verdict.

Vérification **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import has_contract_permission, load_rbac_contract


class RbacCheckController(BaseController):
    """Starter pédagogique : vérifier une permission contractuelle pour des rôles."""

    @staticmethod
    def index(request: Request) -> Response:
        roles_raw = request.query("roles") or "reader"
        permission = request.query("permission") or "article.create"
        roles = [r.strip() for r in roles_raw.split(",") if r.strip()]
        result = load_rbac_contract(".")
        granted = has_contract_permission(result, roles, permission)
        return BaseController.render(
            "rbac_check/index.html",
            context={"roles": roles_raw, "permission": permission, "granted": granted},
            request=request,
        )
