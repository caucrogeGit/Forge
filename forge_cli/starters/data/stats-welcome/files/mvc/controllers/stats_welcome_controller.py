"""Starter Bonjour Forge Stats — palier 1 du niveau débutant (welcome-stats).

Ticket : STARTER-STATS-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-stats`` : il enregistre des
**événements génériques** (un nom, un libellé, une catégorie, des métadonnées) dans
une table SQL, et permet de les consulter. ``make_event`` crée un événement ;
``STATS_EVENTS_TABLE`` / ``STATS_EVENTS_COLUMNS`` décrivent le stockage.

  ``index``   — `GET /stats-welcome` : réponse texte « Bonjour Forge Stats ».
  ``inspect`` — `GET /stats-welcome/inspect` : table, colonnes et un événement de démo.

Transformation **pure** : aucune base de données. Installe le module :
``pip install --pre forge-mvc-stats``.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import STATS_EVENTS_COLUMNS, STATS_EVENTS_TABLE, make_event


class StatsWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Stats."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Stats")

    @staticmethod
    def inspect(request: Request) -> Response:
        event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
        return Response.json({
            "table": STATS_EVENTS_TABLE,
            "columns": list(STATS_EVENTS_COLUMNS),
            "demo_event": {
                "name": event.name,
                "label": event.label,
                "category": event.category,
                "metadata": event.metadata,
            },
        })
