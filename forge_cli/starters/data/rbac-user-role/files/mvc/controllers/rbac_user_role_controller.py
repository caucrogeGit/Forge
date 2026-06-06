"""Starter Associer un rôle à un utilisateur — palier 1 du niveau avancé (welcome-rbac).

Ticket : STARTER-RBAC-USER-ROLE-001.

Les rôles ne servent que reliés à des **utilisateurs**. ``create_auth_user_role``
construit et **valide** une association ``AuthUserRole`` (couple ``user_id`` /
``role_id``). L'application la persiste ensuite dans la table ``user_roles``.

  ``index`` — `GET /rbac-user-role?user_id=1&role_id=2` : construit l'association.

Aucune base de données dans la démo : on montre la construction/validation de l'objet.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import create_auth_user_role


class RbacUserRoleController(BaseController):
    """Starter pédagogique : construire une association utilisateur ↔ rôle."""

    @staticmethod
    def index(request: Request) -> Response:
        try:
            user_id = int(request.param("user_id") or 1)
            role_id = int(request.param("role_id") or 2)
            association = create_auth_user_role(user_id, role_id)
            context = {
                "user_id": association.user_id,
                "role_id": association.role_id,
                "key": f"{association.user_id}:{association.role_id}",
            }
        except Exception as exc:
            context = {"error": str(exc)}
        return BaseController.render("rbac_user_role/index.html", context=context, request=request)
