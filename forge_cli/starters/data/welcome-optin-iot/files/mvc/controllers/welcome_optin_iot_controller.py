"""Starter Bonjour IoT — premier contact avec Forge IoT.

Ticket : STARTER-WELCOME-IOT-001.

Quatre routes pédagogiques :

  1. ``index`` — ``/welcome-optin-iot``
     Réponse texte simple ``"Bonjour Forge IoT"``. Premier contact.
  2. ``inspect`` — ``/welcome-optin-iot/inspect``
     Sérialise la configuration IoT en JSON, **mot de passe masqué**.
  3. ``events`` — ``/welcome-optin-iot/events``
     Lit les derniers événements via ``IotEventRepository.list_recent``.
     Réponse pédagogique si la table n'est pas encore disponible.
  4. ``find_by_device`` — ``/welcome-optin-iot/device/{site}/{device_id}``
     Lit les événements d'un capteur précis via ``find_by_device``.

Le starter fonctionne **sans broker MQTT** (aucun subscriber n'est
lancé ici) et **sans table créée** (les routes événements détectent et
signalent ce cas au lieu de planter).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.config import load_iot_config
from forge_mvc_iot.storage import IotEventRepository


_STORAGE_NOT_READY = {
    "error": "iot_storage_not_ready",
    "message": (
        "La table iot_events n'est pas encore disponible. "
        "Applique la migration Forge IoT avant de lire les événements."
    ),
}


def _storage_not_ready_response() -> Response:
    return Response.json(_STORAGE_NOT_READY, status=503)


def _config_to_safe_dict(cfg) -> dict:
    """Sérialise IotConfig en dict JSON-friendly avec mot de passe masqué."""
    return {
        "mqtt_host": cfg.mqtt_host,
        "mqtt_port": cfg.mqtt_port,
        "mqtt_topic": cfg.mqtt_topic,
        "mqtt_client_id": cfg.mqtt_client_id,
        "mqtt_username": cfg.mqtt_username,
        "mqtt_password": "***" if cfg.mqtt_password else None,
    }


class WelcomeIotController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge IoT")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_iot_config()
        return Response.json(_config_to_safe_dict(cfg))

    @staticmethod
    def events(request: Request) -> Response:
        repo = IotEventRepository()
        try:
            rows = repo.list_recent(limit=20)
        except Exception:
            # Table absente, base inaccessible, etc. — on reste pédagogique.
            return _storage_not_ready_response()
        return Response.json({"events": rows})

    @staticmethod
    def find_by_device(request: Request) -> Response:
        site = request.route_param("site")
        device_id = request.route_param("device_id")
        repo = IotEventRepository()
        try:
            rows = repo.find_by_device(site, device_id, limit=20)
        except Exception:
            return _storage_not_ready_response()
        return Response.json({
            "site": site,
            "device_id": device_id,
            "events": rows,
        })
