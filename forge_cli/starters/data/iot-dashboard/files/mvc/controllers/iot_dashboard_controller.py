"""Starter Tableau de bord IoT — dernier palier du niveau intermédiaire (welcome-iot).

Ticket : STARTER-IOT-DASHBOARD-001.

Après l'API JSON (côté machine), voici la lecture **côté humain** : une vue HTML
qui affiche les derniers événements dans un tableau.

  ``index`` — `GET /iot-dashboard` : derniers événements via
              ``IotEventRepository.list_recent``, rendus dans un template.

Si la table n'est pas prête, la page affiche un tableau vide plutôt que de
planter. Aucune écriture.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.storage import IotEventRepository


class IotDashboardController(BaseController):
    """Starter pédagogique : afficher les événements IoT dans une page HTML."""

    @staticmethod
    def index(request: Request) -> Response:
        try:
            events = IotEventRepository().list_recent(limit=50)
        except Exception:
            events = []
        return BaseController.render(
            "iot_dashboard/index.html",
            context={"events": events},
            request=request,
        )
