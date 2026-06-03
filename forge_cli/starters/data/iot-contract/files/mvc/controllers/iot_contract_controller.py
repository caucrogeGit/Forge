"""Starter Valider un message IoT — palier 1 du niveau avancé (welcome-iot).

Ticket : STARTER-IOT-CONTRACT-001.

On **bascule vers le réel**. Un message qui arrive d'un vrai capteur via le
broker MQTT doit respecter le **contrat** Forge IoT : topic
``forge/{site}/{device_id}/telemetry`` et payload JSON avec les bons champs.
``parse_message`` applique ce contrat — exactement comme le subscriber en
production.

  ``index``    — `GET  /iot-contract` : formulaire (topic + payload).
  ``validate`` — `POST /iot-contract` : valide via ``parse_message`` et affiche
                 la ``Measurement`` obtenue, ou le **code d'erreur** du contrat.

Aucun broker, aucune base : on apprend les règles que les messages réels doivent
respecter.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.mqtt.contract import ContractError, parse_message


_DEFAULT_TOPIC = "forge/atelier/capteur-1/telemetry"
_DEFAULT_PAYLOAD = '{"kind": "temperature", "value": 21.5, "unit": "C", "timestamp": "2026-06-01T10:00:00Z"}'


class IotContractController(BaseController):
    """Starter pédagogique : valider un message contre le contrat IoT."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "iot_contract/index.html",
            context={
                "csrf_token": BaseController.csrf_token(request),
                "topic": _DEFAULT_TOPIC,
                "payload": _DEFAULT_PAYLOAD,
            },
            request=request,
        )

    @staticmethod
    def validate(request: Request) -> Response:
        topic = (request.form("topic") or "").strip()
        payload = (request.form("payload") or "").strip()
        context = {
            "csrf_token": BaseController.csrf_token(request),
            "topic": topic,
            "payload": payload,
        }
        try:
            measurement = parse_message(topic, payload)
        except ContractError as exc:
            context["error_code"] = exc.code
            context["error"] = exc.message
            return BaseController.render(
                "iot_contract/index.html", context=context, request=request
            )
        context["measurement"] = {
            "site": measurement.site,
            "device_id": measurement.device_id,
            "kind": measurement.kind,
            "value": measurement.value,
            "unit": measurement.unit,
            "timestamp": measurement.timestamp,
        }
        return BaseController.render(
            "iot_contract/index.html", context=context, request=request
        )
