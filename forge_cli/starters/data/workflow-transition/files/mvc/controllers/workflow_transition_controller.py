"""Starter Déclarer les transitions — palier 1 du niveau intermédiaire (welcome-workflow).

Ticket : STARTER-WORKFLOW-TRANSITION-001.

Une **transition** autorise le passage d'un statut à un autre. ``make_transition``
en crée une (``from`` → ``to``) ; ``validate_transitions`` vérifie l'ensemble
(transitions cohérentes, statuts connus). Ce qui n'est **pas** déclaré est interdit.

  ``index`` — `GET /workflow-transition` : affiche les transitions déclarées (validées).

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, make_transition, validate_transitions

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]
_RAW_TRANSITIONS = [
    ("draft", "review"),
    ("review", "published"),
    ("review", "draft"),
    ("published", "archived"),
]


class WorkflowTransitionController(BaseController):
    """Starter pédagogique : déclarer et valider les transitions d'un workflow."""

    @staticmethod
    def index(request: Request) -> Response:
        transitions = validate_transitions(
            [make_transition(f, t) for f, t in _RAW_TRANSITIONS], _STATUSES
        )
        return BaseController.render(
            "workflow_transition/index.html",
            context={"transitions": [(t.from_status, t.to_status) for t in transitions]},
            request=request,
        )
