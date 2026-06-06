"""Starter Rôles de la requête — palier 3 du niveau avancé (progression welcome-rbac).

Ticket : STARTER-RBAC-REQUEST-ROLES-001.

Au runtime, RBAC s'appuie sur les **rôles de la requête courante** (déduits de
l'utilisateur connecté, en session). ``get_request_roles`` retourne ces rôles ;
``get_request_permissions`` les permissions qui en découlent — c'est ce que
``can()`` et les guards consomment en interne.

  ``index`` — `GET /rbac-request-roles` : rôles et permissions de la requête, en JSON.

Sans utilisateur connecté, les deux listes sont **vides** : la requête n'a aucun
droit par défaut (sécurisé par défaut). Aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import get_request_permissions, get_request_roles


class RbacRequestRolesController(BaseController):
    """Starter pédagogique : inspecter rôles et permissions de la requête courante."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.json({
            "roles": get_request_roles(request),
            "permissions": sorted(get_request_permissions(request)),
        })
