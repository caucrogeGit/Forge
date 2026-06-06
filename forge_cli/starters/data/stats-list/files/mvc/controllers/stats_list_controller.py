"""Starter Lister les événements — palier 2 du niveau avancé (welcome-stats).

Ticket : STARTER-STATS-LIST-001.

``list_stats_events`` lit les événements via un ``fetch_all`` **injectable** et
retourne des dicts **normalisés** (métadonnées désérialisées du JSON). Comme la
résolution RBAC, l'injection rend la consultation **testable** sans vraie base. La
démo injecte un ``fetch_all`` factice.

  ``index`` — `GET /stats-list` : événements de démo en JSON.

Aucune base de données réelle : le ``fetch_all`` de démo renvoie des lignes fixes.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import list_stats_events

# Lignes que renverrait la base (metadata est une chaîne JSON, comme en SQL).
_DEMO_ROWS = [
    {"id": 1, "name": "page_view", "label": "Vue de page", "category": "navigation",
     "metadata": '{"path": "/"}', "created_at": "2026-01-01T10:00:00"},
    {"id": 2, "name": "user_signup", "label": "Inscription", "category": "auth",
     "metadata": "{}", "created_at": "2026-01-01T11:00:00"},
]


def _demo_fetch_all(sql, params):
    return _DEMO_ROWS


class StatsListController(BaseController):
    """Starter pédagogique : lister les événements via un fetch_all injecté."""

    @staticmethod
    def index(request: Request) -> Response:
        events = list_stats_events(_demo_fetch_all, limit=20)
        return Response.json({"events": events})
