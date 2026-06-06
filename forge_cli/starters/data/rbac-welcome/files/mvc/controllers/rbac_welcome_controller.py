"""Starter Bonjour Forge RBAC — palier 1 du niveau débutant (progression welcome-rbac).

Ticket : STARTER-RBAC-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-rbac`` : Forge sépare les
**rôles** (qui on est) des **permissions** (ce qu'on a le droit de faire), via un
**contrat déclaratif** ``mvc/security/rbac.json`` (ADR-014). Ce starter livre un
contrat de démonstration et l'inspecte.

  ``index``   — `GET /rbac-welcome` : réponse texte « Bonjour Forge RBAC ».
  ``inspect`` — `GET /rbac-welcome/inspect` : contrat chargé (rôles, entités, et
                permissions accordées au rôle ``admin``).

Aucune base de données. Installe le module : ``pip install --pre forge-mvc-rbac``.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import get_contract_permissions, load_rbac_contract


def _inspect() -> dict:
    result = load_rbac_contract(".")
    return {
        "contract_exists": result.exists,
        "valid": result.valid,
        "roles_count": result.roles_count,
        "entities_count": result.entities_count,
        "admin_permissions": sorted(get_contract_permissions(result, ["admin"])),
    }


class RbacWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge RBAC."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge RBAC")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_inspect())
