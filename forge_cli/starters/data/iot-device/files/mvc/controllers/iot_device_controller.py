"""Starter Les événements d'un capteur — palier 3 du niveau débutant (welcome-iot).

Ticket : STARTER-IOT-DEVICE-001.

Après le flux global (palier *Lire les événements IoT*), on **cible un capteur
précis**. La route est paramétrée par ``site`` et ``device_id`` :

  ``index`` — `GET /iot-device/{site}/{device_id}` : événements du capteur
              (``find_by_device``) **et** leur nombre (``count_by_device``).

Réponse ``503`` pédagogique si la table ``iot_events`` n'existe pas encore.
Lecture seule, aucun broker.
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


class IotDeviceController(BaseController):
    """Starter pédagogique : lire les événements d'un capteur précis."""

    @staticmethod
    def index(request: Request) -> Response:
        site = request.route_param("site")
        device_id = request.route_param("device_id")
        repo = IotEventRepository()
        try:
            events = repo.find_by_device(site, device_id, limit=20)
            count = repo.count_by_device(site, device_id)
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({
            "site": site,
            "device_id": device_id,
            "count": count,
            "events": events,
        })
