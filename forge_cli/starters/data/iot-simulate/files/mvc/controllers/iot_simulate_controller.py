"""Starter Simuler une mesure IoT — palier 1 du niveau intermédiaire (welcome-iot).

Ticket : STARTER-IOT-SIMULATE-001.

En vrai, les mesures arrivent d'un capteur via un broker MQTT. Pour **apprendre
sans infrastructure**, on simule : un formulaire compose une mesure, on la
**valide contre le contrat IoT** (``build_payload`` + ``parse_message``), puis on
l'insère dans ``iot_events`` via ``IotEventRepository.insert``. Aucun broker.

  ``index``    — `GET  /iot-simulate` : formulaire + liste des derniers événements.
  ``simulate`` — `POST /iot-simulate` : compose, valide et insère une mesure,
                 puis redirige (POST-Redirect-GET).

C'est la même validation que le subscriber MQTT utilise en production — on
emprunte juste un autre chemin d'entrée.
"""
import json

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.cli.simulate import build_payload, build_topic, utc_timestamp
from forge_mvc_iot.mqtt.contract import ContractError, parse_message
from forge_mvc_iot.storage import IotEventRepository


class IotSimulateController(BaseController):
    """Starter pédagogique : injecter une mesure simulée, validée, sans broker."""

    @staticmethod
    def index(request: Request) -> Response:
        return IotSimulateController._page(request)

    @staticmethod
    def simulate(request: Request) -> Response:
        site = (request.form("site") or "atelier").strip()
        device_id = (request.form("device_id") or "capteur-1").strip()
        kind = (request.form("kind") or "temperature").strip()
        unit = (request.form("unit") or "C").strip()
        raw_value = (request.form("value") or "").strip()
        try:
            value = float(raw_value)
        except ValueError:
            return IotSimulateController._page(
                request, error="La valeur doit être un nombre."
            )
        try:
            topic = build_topic(site, device_id)
            payload = build_payload(
                kind=kind, value=value, unit=unit, timestamp=utc_timestamp()
            )
            measurement = parse_message(topic, json.dumps(payload))
            IotEventRepository().insert(measurement)
        except ContractError as exc:
            return IotSimulateController._page(request, error=str(exc))
        return BaseController.redirect("/iot-simulate")

    @staticmethod
    def _page(request: Request, error: str | None = None) -> Response:
        try:
            events = IotEventRepository().list_recent(limit=20)
        except Exception:
            events = []
        context = {
            "events": events,
            "csrf_token": BaseController.csrf_token(request),
        }
        if error:
            context["error"] = error
        return BaseController.render(
            "iot_simulate/index.html", context=context, request=request
        )
