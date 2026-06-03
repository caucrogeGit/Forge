"""Starter Bonjour Forge IoT — palier 1 du niveau débutant (progression welcome-iot).

Ticket : STARTER-IOT-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-iot``. Deux routes :

  ``index``   — `GET /iot-welcome` : réponse texte « Bonjour Forge IoT ».
  ``inspect`` — `GET /iot-welcome/inspect` : sérialise la configuration MQTT
                lue par ``load_iot_config`` en JSON, **mot de passe masqué**.

Aucun broker MQTT, aucune base de données : on découvre simplement que le module
est installé et comment il est configuré. Installez d'abord le module :
``forge opt-in:install iot`` (ou ``pip install forge-mvc-iot``).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.config import load_iot_config


def _config_to_safe_dict(cfg) -> dict:
    """Sérialise la config IoT en dict JSON, mot de passe **masqué**."""
    return {
        "mqtt_host": cfg.mqtt_host,
        "mqtt_port": cfg.mqtt_port,
        "mqtt_topic": cfg.mqtt_topic,
        "mqtt_client_id": cfg.mqtt_client_id,
        "mqtt_username": cfg.mqtt_username,
        "mqtt_password": "***" if cfg.mqtt_password else None,
    }


class IotWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge IoT."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge IoT")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_iot_config()
        return Response.json(_config_to_safe_dict(cfg))
