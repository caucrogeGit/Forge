"""Starter Bonjour Forge Audio — palier 1 du niveau débutant (progression welcome-audio).

Ticket : STARTER-AUDIO-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-audio`` : une chaîne audio
**sans état** (aucune base de données) — upload, sondage ffprobe, transcodage MP3
ffmpeg, lecture en streaming.

  ``index``   — `GET /audio-welcome` : réponse texte « Bonjour Forge Audio ».
  ``inspect`` — `GET /audio-welcome/inspect` : configuration (stockage, limites,
                binaires) en JSON, **token masqué**.

Aucune base de données. Installe d'abord le module depuis les sources :
``pip install -e packages/forge-mvc-audio/`` (``ffmpeg``/``ffprobe`` sont des
binaires système, pas des dépendances pip).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import load_audio_config


def _config_to_safe_dict(cfg) -> dict:
    """Sérialise la config audio, **token masqué**."""
    return {
        "storage_root": cfg.storage_root,
        "max_upload_mb": cfg.max_upload_mb,
        "max_duration_seconds": cfg.max_duration_seconds,
        "ffprobe_bin": cfg.ffprobe_bin,
        "ffmpeg_bin": cfg.ffmpeg_bin,
        "api_token": "***" if cfg.api_token else None,
    }


class AudioWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Audio."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Audio")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_config_to_safe_dict(load_audio_config()))
