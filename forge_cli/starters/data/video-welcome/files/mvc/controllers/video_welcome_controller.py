"""Starter Bonjour Forge Vidéo — palier 1 du niveau débutant (welcome-video).

Ticket : STARTER-VIDEO-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-video``. Deux routes :

  ``index``   — `GET /video-welcome` : réponse texte « Bonjour Forge Vidéo ».
  ``inspect`` — `GET /video-welcome/inspect` : sérialise la configuration vidéo
                lue par ``load_video_config`` en JSON, **token masqué**.

Aucun ffmpeg, aucune base de données : on découvre que le module est installé et
comment il est configuré. Installez-le d'abord : ``forge opt-in:install video``
(ou ``pip install forge-mvc-video``).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.config import load_video_config


def _config_to_safe_dict(cfg) -> dict:
    """Sérialise la config vidéo en dict JSON, token **masqué**."""
    return {
        "ffmpeg_bin": cfg.ffmpeg_bin,
        "ffprobe_bin": cfg.ffprobe_bin,
        "storage_root": str(cfg.storage_root),
        "max_upload_mb": cfg.max_upload_mb,
        "max_duration_seconds": cfg.max_duration_seconds,
        "api_token": "***" if cfg.api_token else None,
    }


class VideoWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Vidéo."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Vidéo")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_video_config()
        return Response.json(_config_to_safe_dict(cfg))
