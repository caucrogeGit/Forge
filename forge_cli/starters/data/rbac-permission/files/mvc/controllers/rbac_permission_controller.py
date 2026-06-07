"""Starter Code de permission — palier 2 du niveau débutant (progression welcome-rbac).

Ticket : STARTER-RBAC-PERMISSION-001.

Une **permission** est un code en **notation pointée** (``entité.action``, p. ex.
``article.create``). ``normalize_permission_code`` le met en forme (minuscules,
points) ; ``validate_permission`` refuse les codes invalides (vides, avec espaces…).

  ``index`` — `GET /rbac-permission?code=...` : normalise un code et indique s'il
              est valide.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import RbacValidationError, normalize_permission_code, validate_permission

_DEMO_CODE = "Article.Create"


def _permission_view(code: str) -> dict:
    normalized = normalize_permission_code(code)
    try:
        validate_permission(normalized)
        return {"input": code, "normalized": normalized, "valid": True, "error": None}
    except RbacValidationError as exc:
        return {"input": code, "normalized": normalized, "valid": False, "error": str(exc)}


class RbacPermissionController(BaseController):
    """Starter pédagogique : normaliser et valider un code de permission."""

    @staticmethod
    def index(request: Request) -> Response:
        code = request.query("code") or _DEMO_CODE
        return BaseController.render(
            "rbac_permission/index.html", context=_permission_view(code), request=request
        )
