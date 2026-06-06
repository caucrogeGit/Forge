"""Starter Le SQL de consultation — palier 1 du niveau avancé (welcome-stats).

Ticket : STARTER-STATS-ADMIN-SQL-001.

Pour **consulter** les événements, ``get_stats_events_admin_sql`` construit un
``SELECT`` filtrable (par nom, par catégorie, avec une limite) et
``prepare_stats_events_admin_params`` fournit ses paramètres liés. SQL visible,
filtres paramétrés (anti-injection).

  ``index`` — `GET /stats-admin-sql?category=...` : le SELECT et ses paramètres.

Transformation **pure** : aucune base de données (on montre le SQL, on ne l'exécute pas).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import get_stats_events_admin_sql, prepare_stats_events_admin_params


class StatsAdminSqlController(BaseController):
    """Starter pédagogique : voir le SQL de consultation des événements."""

    @staticmethod
    def index(request: Request) -> Response:
        category = request.param("category") or None
        return BaseController.render(
            "stats_admin_sql/index.html",
            context={
                "category": category or "(toutes)",
                "sql": get_stats_events_admin_sql(category=category, limit=20),
                "params": list(prepare_stats_events_admin_params(category=category, limit=20)),
            },
            request=request,
        )
