"""Starter Normaliser une ligne — palier 3 du niveau avancé (welcome-stats).

Ticket : STARTER-STATS-NORMALIZE-001.

En base, les métadonnées sont stockées en **chaîne JSON**. ``normalize_stats_event_row``
transforme une ligne brute en dict propre, **métadonnées désérialisées** en objet —
prêt à afficher. Une ligne incomplète ou un JSON invalide lève ``StatsAdminError``.

  ``index`` — `GET /stats-normalize` : une ligne brute et sa version normalisée.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import normalize_stats_event_row

_RAW_ROW = {
    "id": 1,
    "name": "page_view",
    "label": "Vue de page",
    "category": "navigation",
    "metadata": '{"path": "/", "ref": "home"}',
    "created_at": "2026-01-01T10:00:00",
}


class StatsNormalizeController(BaseController):
    """Starter pédagogique : normaliser une ligne d'événement de la base."""

    @staticmethod
    def index(request: Request) -> Response:
        normalized = normalize_stats_event_row(dict(_RAW_ROW))
        return BaseController.render(
            "stats_normalize/index.html",
            context={
                "raw_metadata": _RAW_ROW["metadata"],
                "normalized_metadata": normalized["metadata"],
                "name": normalized["name"],
            },
            request=request,
        )
