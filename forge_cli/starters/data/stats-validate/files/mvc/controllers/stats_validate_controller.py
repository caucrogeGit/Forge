"""Starter Valider un événement — palier 3 du niveau intermédiaire (welcome-stats).

Ticket : STARTER-STATS-VALIDATE-001.

Un événement est **validé à la construction** (``make_event``) et peut être
re-vérifié (``validate_event``). Un nom invalide ou un événement mal formé lève
``StatsEventError`` — on refuse **avant** d'écrire en base.

  ``index`` — `GET /stats-validate?name=...` : construit et valide un événement.

Transformation **pure** : aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_stats import StatsEventError, make_event, validate_event

_DEMO_NAME = "page_view"


def _validate_view(name: str) -> dict:
    try:
        event = make_event(name, "Démo", "general", {})
        validate_event(event)
        return {"input": name, "valid": True, "name": event.name, "error": None}
    except StatsEventError as exc:
        return {"input": name, "valid": False, "name": None, "error": str(exc)}


class StatsValidateController(BaseController):
    """Starter pédagogique : valider un événement avant de l'enregistrer."""

    @staticmethod
    def index(request: Request) -> Response:
        name = request.query("name") or _DEMO_NAME
        return BaseController.render(
            "stats_validate/index.html", context=_validate_view(name), request=request
        )
