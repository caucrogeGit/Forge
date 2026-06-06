"""Starter Bonjour Forge Workflow — palier 1 du niveau débutant (welcome-workflow).

Ticket : STARTER-WORKFLOW-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-workflow`` : une machine à
états applicative (statuts + transitions). Un **statut** porte un nom, un libellé,
une couleur, et des marqueurs ``is_initial`` / ``is_final``. ``validate_statuses``
vérifie l'ensemble (pas de doublon, au plus un statut initial).

  ``index``   — `GET /workflow-welcome` : réponse texte « Bonjour Forge Workflow ».
  ``inspect`` — `GET /workflow-welcome/inspect` : le jeu de statuts de démo en JSON.

Transformation **pure** : aucune base de données. Installe le module :
``pip install --pre forge-mvc-workflow``.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_workflow import make_status, validate_statuses


def _demo_statuses():
    """Workflow de publication de démonstration."""
    return validate_statuses([
        make_status("draft", "Brouillon", "gray", is_initial=True),
        make_status("review", "En revue", "yellow"),
        make_status("published", "Publié", "green"),
        make_status("archived", "Archivé", "red", is_final=True),
    ])


class WorkflowWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Workflow."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Workflow")

    @staticmethod
    def inspect(request: Request) -> Response:
        statuses = _demo_statuses()
        return Response.json({
            "count": len(statuses),
            "statuses": [
                {
                    "name": s.name,
                    "label": s.label,
                    "color": s.color,
                    "is_initial": s.is_initial,
                    "is_final": s.is_final,
                }
                for s in statuses
            ],
        })
