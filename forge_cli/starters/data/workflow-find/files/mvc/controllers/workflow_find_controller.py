"""Starter Retrouver un statut — palier 3 du niveau débutant (welcome-workflow).

Ticket : STARTER-WORKFLOW-FIND-001.

``find_status`` localise un statut **par son nom** dans un jeu de statuts, ou
retourne ``None`` s'il n'existe pas — utile avant d'autoriser une action sur un
objet dont on connaît le nom de statut courant.

  ``index`` — `GET /workflow-find?name=...` : retrouve le statut (ou « introuvable »).

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import find_status, make_status, normalize_status_name

_STATUSES = [
    make_status("draft", "Brouillon", "gray", is_initial=True),
    make_status("review", "En revue", "yellow"),
    make_status("published", "Publié", "green"),
    make_status("archived", "Archivé", "red", is_final=True),
]


class WorkflowFindController(BaseController):
    """Starter pédagogique : retrouver un statut par son nom."""

    @staticmethod
    def index(request: Request) -> Response:
        name = normalize_status_name(request.query("name") or "review")
        found = find_status(_STATUSES, name)
        return BaseController.render(
            "workflow_find/index.html",
            context={
                "name": name,
                "found": found is not None,
                "label": found.label if found else None,
                "color": found.color if found else None,
            },
            request=request,
        )
