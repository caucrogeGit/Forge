"""Starter Transitions disponibles — palier 3 du niveau intermédiaire (welcome-workflow).

Ticket : STARTER-WORKFLOW-AVAILABLE-001.

``get_available_transitions`` répond à « depuis ce statut, où puis-je aller ? ». Il
liste les transitions partant du statut courant — idéal pour générer dynamiquement
les **boutons d'action** d'une fiche, sans coder chaque cas en dur.

  ``index`` — `GET /workflow-available?from=review` : statuts atteignables.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import get_available_transitions, make_transition

_TRANSITIONS = [
    make_transition("draft", "review"),
    make_transition("review", "published"),
    make_transition("review", "draft"),
    make_transition("published", "archived"),
]


class WorkflowAvailableController(BaseController):
    """Starter pédagogique : lister les transitions possibles depuis un statut."""

    @staticmethod
    def index(request: Request) -> Response:
        from_name = request.query("from") or "review"
        available = get_available_transitions(_TRANSITIONS, from_name)
        return BaseController.render(
            "workflow_available/index.html",
            context={"from_name": from_name, "targets": [t.to_status for t in available]},
            request=request,
        )
