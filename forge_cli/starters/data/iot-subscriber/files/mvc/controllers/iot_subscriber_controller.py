"""Starter Le subscriber MQTT — palier 2 du niveau avancé (welcome-iot).

Ticket : STARTER-IOT-SUBSCRIBER-001.

Le **vrai temps réel**. En production, un broker MQTT pousse les messages des
capteurs. La commande ``forge iot:listen`` lance un ``MqttSubscriber`` qui, pour
chaque message reçu, **valide** (``parse_message``) puis **stocke**
(``IotEventRepository.insert``) :

    Mosquitto → forge iot:listen → MqttSubscriber → parse_message → insert

Recevoir de vrais messages demande un **broker** (à la charge du lecteur). Cette
route ne lance pas le subscriber : elle affiche la **configuration broker
effective** (TLS comprise) pour la vérifier avant de lancer ``forge iot:listen``.

  ``index`` — `GET /iot-subscriber` : récapitule la config de connexion broker.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.config import load_iot_config


class IotSubscriberController(BaseController):
    """Starter pédagogique : visualiser la config broker avant `iot:listen`."""

    @staticmethod
    def index(request: Request) -> Response:
        cfg = load_iot_config()
        return BaseController.render(
            "iot_subscriber/index.html",
            context={
                "broker": f"{cfg.mqtt_host}:{cfg.mqtt_port}",
                "topic": cfg.mqtt_topic,
                "tls_enabled": cfg.mqtt_tls_enabled,
            },
            request=request,
        )
