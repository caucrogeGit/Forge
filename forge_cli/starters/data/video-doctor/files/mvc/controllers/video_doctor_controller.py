"""Starter Diagnostiquer le module Vidéo — dernier palier du niveau avancé (welcome-video).

Ticket : STARTER-VIDEO-DOCTOR-001.

Exploiter un module en production, c'est aussi savoir **diagnostiquer**. Forge
Vidéo fournit ``forge video:doctor`` ; cette route en expose le **sous-ensemble
non invasif** (sans toucher à la base) :

  ``index`` — `GET /video-doctor` : vérifie « paquet importable », « configuration
              chargeable », « migration présente » et la **présence de ffprobe /
              ffmpeg** (indispensables au transcodage), puis renvoie le statut en
              JSON.

Le diagnostic **complet** (table en base) reste la commande
``forge video:doctor``. Sans base.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.cli.doctor import (
    check_config_loadable,
    check_ffmpeg_present,
    check_ffprobe_present,
    check_migration_present,
    check_package_importable,
)


# Vérifications sûres : aucune ne touche la base. Les contrôles ffprobe/ffmpeg
# se contentent de localiser les binaires (essentiels au transcodage).
_SAFE_CHECKS = (
    check_package_importable,
    check_config_loadable,
    check_migration_present,
    check_ffprobe_present,
    check_ffmpeg_present,
)


class VideoDoctorController(BaseController):
    """Starter pédagogique : diagnostic Vidéo non invasif exposé en JSON."""

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
        healthy = all(c["status"] == "ok" for c in checks)
        return Response.json({"healthy": healthy, "checks": checks})
