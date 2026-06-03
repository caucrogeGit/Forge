"""Starter Lire les événements IoT — palier 2 du niveau débutant (welcome-iot).

Ticket : STARTER-IOT-EVENTS-001.

Le module Forge IoT stocke les mesures reçues dans la table ``iot_events``. Ce
palier les **lit** via ``IotEventRepository.list_recent`` et les renvoie en JSON.

  ``index`` — `GET /iot-events` : derniers événements, ordre du plus récent.

Le starter reste **pédagogique** quand la table n'existe pas encore (aucun
``iot:init`` lancé) : au lieu de planter, il renvoie une réponse ``503`` claire
qui explique la marche à suivre. Aucun broker, aucune écriture.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.storage import IotEventRepository


_STORAGE_NOT_READY = {
    "error": "iot_storage_not_ready",
    "message": (
        "La table iot_events n'est pas encore disponible. "
        "Applique la migration Forge IoT (forge iot:init) avant de lire "
        "les événements."
    ),
}


class IotEventsController(BaseController):
    """Starter pédagogique : lire les derniers événements IoT stockés."""

    @staticmethod
    def index(request: Request) -> Response:
        repo = IotEventRepository()
        try:
            events = repo.list_recent(limit=20)
        except Exception:
            # Table absente, base inaccessible… — on reste pédagogique.
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"events": events})
