"""Starter Bonjour Vidéo — premier contact avec Forge Video.

Ticket : STARTER-WELCOME-VIDEO-001.

Trois routes pédagogiques :

  1. ``index`` — ``/welcome-optin-video``
     Réponse texte simple ``"Bonjour Forge Video"``. Premier contact.
  2. ``inspect`` — ``/welcome-optin-video/inspect``
     Sérialise la configuration vidéo en JSON, **token masqué**.
  3. ``list`` — ``/welcome-optin-video/list``
     Liste les dernières vidéos via ``VideoRepository.list_recent``.
     Réponse pédagogique si la table ``videos`` n'est pas encore disponible.

La route de lecture officielle ``GET /videos/{uuid}`` (streaming HTTP Range)
est branchée séparément via ``optins/video/routes.py``. Le starter fonctionne
**sans ffmpeg** (aucun transcodage ici) et **sans table créée** (la route
``list`` détecte et signale ce cas au lieu de planter).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.config import load_video_config
from forge_mvc_video.storage.repository import VideoRepository


_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Video avant de lister les vidéos "
        "(forge video:init && forge migration:apply)."
    ),
}


def _storage_not_ready_response() -> Response:
    return Response.json(_STORAGE_NOT_READY, status=503)


def _config_to_safe_dict(cfg) -> dict:
    """Sérialise VideoConfig en dict JSON-friendly avec token masqué."""
    return {
        "ffmpeg_bin": cfg.ffmpeg_bin,
        "ffprobe_bin": cfg.ffprobe_bin,
        "storage_root": cfg.storage_root,
        "max_upload_mb": cfg.max_upload_mb,
        "max_duration_seconds": cfg.max_duration_seconds,
        "api_token": "***" if cfg.api_token else None,
    }


class WelcomeVideoController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Video")

    @staticmethod
    def inspect(request: Request) -> Response:
        cfg = load_video_config()
        return Response.json(_config_to_safe_dict(cfg))

    @staticmethod
    def list(request: Request) -> Response:
        repo = VideoRepository()
        try:
            rows = repo.list_recent(limit=20)
        except Exception:
            # Table absente, base inaccessible, etc. — on reste pédagogique.
            return _storage_not_ready_response()
        return Response.json({"videos": rows})
