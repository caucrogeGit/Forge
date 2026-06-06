"""Starter Enregistrer un événement — palier 2 du niveau intermédiaire (welcome-stats).

Ticket : STARTER-STATS-TRACK-001.

``track_event`` enregistre un événement. Comme la résolution RBAC, il prend un
**exécuteur injectable** (``execute``) plutôt que d'accéder directement à la base —
ce qui le rend **testable** sans vraie base. La démo injecte un exécuteur factice ;
en production on passe ``core.database.db.execute``.

  ``index`` — `GET /stats-track` : enregistre un événement de démo et montre ce qui
              aurait été exécuté.

Aucune base de données réelle : l'exécuteur de démo capture la requête.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import make_event, track_event


class StatsTrackController(BaseController):
    """Starter pédagogique : enregistrer un événement via un exécuteur injecté."""

    @staticmethod
    def index(request: Request) -> Response:
        captured = []

        def _demo_execute(sql, params):
            captured.append({"sql": sql, "params": list(params)})
            return 1

        event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
        track_event(_demo_execute, event)
        return BaseController.render(
            "stats_track/index.html", context={"executed": captured[0]}, request=request
        )
