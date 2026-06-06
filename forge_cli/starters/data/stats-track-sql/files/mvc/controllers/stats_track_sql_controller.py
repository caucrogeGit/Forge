"""Starter Le SQL d'insertion — palier 1 du niveau intermédiaire (welcome-stats).

Ticket : STARTER-STATS-TRACK-SQL-001.

Avant d'exécuter, on **voit** le SQL. ``get_track_event_sql`` retourne l'``INSERT``
paramétré ; ``prepare_track_event_values`` retourne le tuple de valeurs pour un
événement (métadonnées sérialisées en JSON). SQL visible, requête paramétrée (anti
injection), aucun ORM.

  ``index`` — `GET /stats-track-sql` : l'INSERT et les valeurs pour un événement de démo.

Transformation **pure** : aucune base de données (on montre, on n'exécute pas).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import get_track_event_sql, make_event, prepare_track_event_values


class StatsTrackSqlController(BaseController):
    """Starter pédagogique : voir le SQL d'insertion d'un événement."""

    @staticmethod
    def index(request: Request) -> Response:
        event = make_event("page_view", "Vue de page", "navigation", {"path": "/"})
        return BaseController.render(
            "stats_track_sql/index.html",
            context={
                "sql": get_track_event_sql(),
                "values": list(prepare_track_event_values(event)),
            },
            request=request,
        )
