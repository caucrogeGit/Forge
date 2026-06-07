"""Starter Vérifier une transition — palier 2 du niveau intermédiaire (welcome-workflow).

Ticket : STARTER-WORKFLOW-CHECK-001.

``can_transition`` répond à « peut-on passer de ce statut à cet autre ? » selon les
transitions déclarées. C'est le contrôle à poser **avant** d'appliquer un changement
de statut à un objet.

  ``index`` — `GET /workflow-check?from=draft&to=published` : autorisé / refusé.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import can_transition, make_transition

_TRANSITIONS = [
    make_transition("draft", "review"),
    make_transition("review", "published"),
    make_transition("review", "draft"),
    make_transition("published", "archived"),
]


class WorkflowCheckController(BaseController):
    """Starter pédagogique : vérifier qu'une transition est autorisée."""

    @staticmethod
    def index(request: Request) -> Response:
        from_name = request.query("from") or "draft"
        to_name = request.query("to") or "published"
        allowed = can_transition(_TRANSITIONS, from_name, to_name)
        return BaseController.render(
            "workflow_check/index.html",
            context={"from_name": from_name, "to_name": to_name, "allowed": allowed},
            request=request,
        )
