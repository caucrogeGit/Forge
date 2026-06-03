"""Starter Diagnostiquer le module IoT — dernier palier du niveau avancé (welcome-iot).

Ticket : STARTER-IOT-DOCTOR-001.

Exploiter un module en production, c'est aussi savoir **diagnostiquer** quand
quelque chose cloche. Forge IoT fournit ``forge iot:doctor`` ; cette route en
expose le **sous-ensemble non invasif** (sans toucher à la base ni au broker) :

  ``index`` — `GET /iot-doctor` : exécute les vérifications « paquet importable »,
              « configuration chargeable » et « API HTTP enregistrable », et
              renvoie leur statut en JSON.

Le diagnostic **complet** (table en base, connexion broker) reste la commande
``forge iot:doctor`` (avec ``--db`` / ``--mqtt``). Sans base, sans broker.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_iot.cli.doctor import (
    check_config_loadable,
    check_http_api_registrable,
    check_package_importable,
)


# Vérifications sûres : aucune ne touche la base ni le broker.
_SAFE_CHECKS = (
    check_package_importable,
    check_config_loadable,
    check_http_api_registrable,
)


class IotDoctorController(BaseController):
    """Starter pédagogique : diagnostic IoT non invasif exposé en JSON."""

    @staticmethod
    def index(request: Request) -> Response:
        checks = []
        for check in _SAFE_CHECKS:
            result = check()
            checks.append({
                "status": result.status,
                "label": result.label,
                "detail": result.detail,
            })
        healthy = all(c["status"] == "ok" for c in checks)
        return Response.json({"healthy": healthy, "checks": checks})
