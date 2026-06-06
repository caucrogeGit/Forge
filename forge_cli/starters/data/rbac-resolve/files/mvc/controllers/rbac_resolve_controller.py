"""Starter Résoudre les permissions d'un utilisateur — palier 2 du niveau avancé (welcome-rbac).

Ticket : STARTER-RBAC-RESOLVE-001.

En production, les permissions d'un utilisateur viennent de la **base** (ses rôles ×
les permissions de ces rôles). ``get_user_permissions`` et ``user_has_permission``
font ce calcul via un ``fetch_all`` **injectable** — ce qui les rend testables sans
vraie base. On injecte ici un ``fetch_all`` de démonstration.

  ``index`` — `GET /rbac-resolve` : permissions effectives de l'utilisateur démo + deux
              vérifications, en JSON.

Aucune base de données réelle : le ``fetch_all`` de démo renvoie des lignes fixes.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import get_user_permissions, user_has_permission

_DEMO_USER_ID = 1
# Lignes que renverrait la base pour les permissions de l'utilisateur démo.
_DEMO_ROWS = [{"code": "article.list"}, {"code": "article.show"}, {"code": "article.create"}]


def _demo_fetch_all(sql, params=()):
    """fetch_all de démonstration : renvoie des permissions fixes (au lieu de la base)."""
    return _DEMO_ROWS


class RbacResolveController(BaseController):
    """Starter pédagogique : résoudre les permissions effectives d'un utilisateur."""

    @staticmethod
    def index(request: Request) -> Response:
        perms = get_user_permissions(_DEMO_USER_ID, fetch_all=_demo_fetch_all)
        return Response.json({
            "user_id": _DEMO_USER_ID,
            "permissions": list(perms),
            "can_create": user_has_permission(_DEMO_USER_ID, "article.create", fetch_all=_demo_fetch_all),
            "can_delete": user_has_permission(_DEMO_USER_ID, "article.delete", fetch_all=_demo_fetch_all),
        })
