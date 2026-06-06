"""Starter Le schéma SQL — palier 3 du niveau débutant (welcome-stats).

Ticket : STARTER-STATS-SCHEMA-001.

Fidèle à la charte (principe 5, « garder SQL visible »), Forge Stats **n'a pas
d'ORM** : il expose directement le ``CREATE TABLE`` de ``forge_stats_events`` via
``get_stats_events_schema_sql``. On lit le schéma exact qui sera créé en base.

  ``index`` — `GET /stats-schema` : affiche le SQL du schéma et la liste des colonnes.

Transformation **pure** : aucune base de données (on montre le SQL, on ne l'exécute pas).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import STATS_EVENTS_COLUMNS, STATS_EVENTS_TABLE, get_stats_events_schema_sql


class StatsSchemaController(BaseController):
    """Starter pédagogique : lire le schéma SQL des statistiques."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "stats_schema/index.html",
            context={
                "table": STATS_EVENTS_TABLE,
                "columns": list(STATS_EVENTS_COLUMNS),
                "schema_sql": get_stats_events_schema_sql(),
            },
            request=request,
        )
