"""Starter Nom de statut — palier 2 du niveau débutant (welcome-workflow).

Ticket : STARTER-WORKFLOW-STATUS-001.

Un **nom de statut** est un identifiant stable en ``snake_case``.
``normalize_status_name`` le met en forme (« En Revue » → ``en_revue``) ;
``validate_status_name`` refuse les noms invalides.

  ``index`` — `GET /workflow-status?name=...` : normalise et valide un nom.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import WorkflowStatusError, normalize_status_name, validate_status_name

_DEMO_NAME = "En Revue"


def _status_view(raw: str) -> dict:
    normalized = normalize_status_name(raw)
    try:
        validate_status_name(raw)
        return {"input": raw, "normalized": normalized, "valid": True, "error": None}
    except WorkflowStatusError as exc:
        return {"input": raw, "normalized": normalized, "valid": False, "error": str(exc)}


class WorkflowStatusController(BaseController):
    """Starter pédagogique : normaliser et valider un nom de statut."""

    @staticmethod
    def index(request: Request) -> Response:
        raw = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "workflow_status/index.html", context=_status_view(raw), request=request
        )
