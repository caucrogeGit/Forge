"""Starter Badge de statut — palier 1 du niveau avancé (welcome-workflow).

Ticket : STARTER-WORKFLOW-BADGE-001.

Un statut, ça s'**affiche**. ``workflow_status_badge`` produit un badge HTML **sûr**
(``Markup`` : Jinja ne le double-échappe pas) à partir d'un statut — couleur et
libellé inclus. Plus besoin de bricoler le HTML dans chaque vue.

  ``index`` — `GET /workflow-badge` : affiche un badge pour chaque statut de démo.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, workflow_status_badge

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]


class WorkflowBadgeController(BaseController):
    """Starter pédagogique : afficher un badge HTML de statut."""

    @staticmethod
    def index(request: Request) -> Response:
        badges = [(s.name, workflow_status_badge(s)) for s in _STATUSES]
        return BaseController.render(
            "workflow_badge/index.html", context={"badges": badges}, request=request
        )
