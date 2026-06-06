"""Starter Helpers Workflow dans Jinja — palier 3 du niveau avancé (welcome-workflow).

Ticket : STARTER-WORKFLOW-JINJA-001.

Pour utiliser les helpers de statut **directement dans un template**,
``make_workflow_jinja_helpers`` retourne un dict prêt à injecter
(``workflow_status_badge``, ``workflow_status_label``, ``workflow_status_color``,
``workflow_status_badge_class``). Contrairement à RBAC, ils ne sont **pas**
auto-enregistrés : on les ajoute au contexte de la vue.

  ``index`` — `GET /workflow-jinja` : injecte les helpers et les utilise dans la vue.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, make_workflow_jinja_helpers

_DEMO_STATUS = make_status("review", "En revue", "yellow")


class WorkflowJinjaController(BaseController):
    """Starter pédagogique : injecter les helpers Workflow dans un template."""

    @staticmethod
    def index(request: Request) -> Response:
        context = {"status": _DEMO_STATUS}
        context.update(make_workflow_jinja_helpers())
        return BaseController.render(
            "workflow_jinja/index.html", context=context, request=request
        )
