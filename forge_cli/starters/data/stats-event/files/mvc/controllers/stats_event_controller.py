"""Starter Nom d'événement — palier 2 du niveau débutant (welcome-stats).

Ticket : STARTER-STATS-EVENT-001.

Un **nom d'événement** est un identifiant ``snake_case`` (lettres, chiffres,
espaces et tirets, convertis en underscores). ``normalize_event_name`` le met en
forme ; ``validate_event_name`` refuse les noms invalides (un point, par exemple).

  ``index`` — `GET /stats-event?name=...` : normalise et valide un nom.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import StatsEventError, normalize_event_name, validate_event_name

_DEMO_NAME = "Page View"


def _event_view(raw: str) -> dict:
    try:
        normalized = normalize_event_name(raw)
        validate_event_name(raw)
        return {"input": raw, "normalized": normalized, "valid": True, "error": None}
    except StatsEventError as exc:
        return {"input": raw, "normalized": None, "valid": False, "error": str(exc)}


class StatsEventController(BaseController):
    """Starter pédagogique : normaliser et valider un nom d'événement."""

    @staticmethod
    def index(request: Request) -> Response:
        raw = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "stats_event/index.html", context=_event_view(raw), request=request
        )
