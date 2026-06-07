"""Starter Rôle et slug — palier 3 du niveau débutant (progression welcome-rbac).

Ticket : STARTER-RBAC-ROLE-001.

Un **rôle** porte un **nom** lisible (« Éditeur en chef ») et un **slug** stable
(``editeur-en-chef``) qui sert d'identifiant. ``normalize_role_slug`` dérive le
slug ; ``validate_role`` refuse un rôle invalide (nom vide, slug avec espaces…).

  ``index`` — `GET /rbac-role?name=...` : dérive le slug et indique la validité.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import RbacValidationError, normalize_role_slug, validate_role

_DEMO_NAME = "Éditeur en chef"


def _role_view(name: str) -> dict:
    slug = normalize_role_slug(name)
    try:
        validate_role(name, slug)
        return {"name": name, "slug": slug, "valid": True, "error": None}
    except RbacValidationError as exc:
        return {"name": name, "slug": slug, "valid": False, "error": str(exc)}


class RbacRoleController(BaseController):
    """Starter pédagogique : dériver et valider un rôle (nom + slug)."""

    @staticmethod
    def index(request: Request) -> Response:
        name = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "rbac_role/index.html", context=_role_view(name), request=request
        )
