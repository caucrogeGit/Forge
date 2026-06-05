"""Starter Diagnostiquer le module Audio — palier 3 du niveau avancé (welcome-audio).

Ticket : STARTER-AUDIO-DOCTOR-001.

Exploiter un module, c'est savoir le **diagnostiquer**. Forge Audio fournit
``forge audio:doctor`` ; cette route en expose le **sous-ensemble non invasif** en
JSON : paquet importable, configuration chargeable, présence de ``ffprobe`` /
``ffmpeg`` (indispensables au sondage et au transcodage), routes enregistrables.

  ``index`` — `GET /audio-doctor` : exécute les contrôles et renvoie le statut JSON.

Aucune base de données (le module est sans état) ; le diagnostic complet reste la
commande ``forge audio:doctor``.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio.cli.doctor import (
    check_config_loadable,
    check_ffmpeg_present,
    check_ffprobe_present,
    check_package_importable,
    check_routes_registrable,
)

# Contrôles sûrs : aucun ne touche de fichier ni de réseau.
_SAFE_CHECKS = (
    check_package_importable,
    check_config_loadable,
    check_ffprobe_present,
    check_ffmpeg_present,
    check_routes_registrable,
)


class AudioDoctorController(BaseController):
    """Starter pédagogique : diagnostic Audio non invasif exposé en JSON."""

    @staticmethod
    def index(request: Request) -> Response:
        checks = []
        for check in _SAFE_CHECKS:
            result = check()
            checks.append({
                "status": result.status,
                "name": result.name,
                "detail": result.detail,
            })
        return Response.json({"checks": checks})
