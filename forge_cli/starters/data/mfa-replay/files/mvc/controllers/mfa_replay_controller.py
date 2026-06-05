"""Starter Anti-rejeu TOTP — palier 2 du niveau avancé (welcome-mfa).

Ticket : STARTER-MFA-REPLAY-001.

Un code TOTP reste valide ~30 s : sans garde, un attaquant qui l'intercepte
pourrait le **rejouer**. ``record_used`` marque une *step* (fenêtre de temps)
consommée pour un facteur ; ``is_replay`` refuse alors sa réutilisation.
``step_for_time`` calcule la step courante.

  ``index`` — `GET  /mfa-replay` : affiche la step courante et si elle est déjà
              consommée pour le facteur démo.
  ``use``   — `POST /mfa-replay` : consomme la step courante puis montre que toute
              réutilisation est refusée.

État **en mémoire** (comme le rate-limit), aucune base de données, aucune clé.
"""
import time

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_mfa import is_replay, record_used, step_for_time

_FACTOR_ID = 1


class MfaReplayController(BaseController):
    """Starter pédagogique : empêcher le rejeu d'un code TOTP."""

    @staticmethod
    def index(request: Request) -> Response:
        step = step_for_time(time.time())
        return BaseController.render(
            "mfa_replay/index.html",
            context={
                "csrf_token": BaseController.csrf_token(request),
                "step": step,
                "replayed": is_replay(_FACTOR_ID, step),
            },
            request=request,
        )

    @staticmethod
    def use(request: Request) -> Response:
        step = step_for_time(time.time())
        already = is_replay(_FACTOR_ID, step)
        if not already:
            record_used(_FACTOR_ID, step)
        return BaseController.render(
            "mfa_replay/index.html",
            context={
                "csrf_token": BaseController.csrf_token(request),
                "step": step,
                "accepted": not already,
                "replayed": is_replay(_FACTOR_ID, step),
            },
            request=request,
        )
