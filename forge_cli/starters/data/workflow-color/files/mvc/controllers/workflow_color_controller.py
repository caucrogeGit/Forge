"""Starter Couleur, libellé, classe — palier 2 du niveau avancé (welcome-workflow).

Ticket : STARTER-WORKFLOW-COLOR-001.

Pour un affichage **sur mesure**, on accède aux pièces du badge :
``workflow_status_label`` (texte), ``workflow_status_color`` (couleur, défaut
``gray``) et ``workflow_status_badge_class`` (classes Tailwind, repli gris si couleur
inconnue). Ces helpers acceptent un statut **ou** une simple chaîne.

  ``index`` — `GET /workflow-color` : libellé, couleur et classes de chaque statut.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import (
    make_status,
    workflow_status_badge_class,
    workflow_status_color,
    workflow_status_label,
)

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]


class WorkflowColorController(BaseController):
    """Starter pédagogique : accéder aux pièces d'un badge de statut."""

    @staticmethod
    def index(request: Request) -> Response:
        rows = [
            {
                "name": s.name,
                "label": workflow_status_label(s),
                "color": workflow_status_color(s),
                "css": workflow_status_badge_class(s),
            }
            for s in _STATUSES
        ]
        return BaseController.render(
            "workflow_color/index.html", context={"rows": rows}, request=request
        )
