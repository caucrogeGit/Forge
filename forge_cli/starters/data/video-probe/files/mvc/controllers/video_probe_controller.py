"""Starter Sonder une vidéo — palier 1 du niveau avancé (welcome-video).

Ticket : STARTER-VIDEO-PROBE-001.

On **bascule vers le réel**. ``probe_video`` lance **ffprobe** (lecture seule) sur
le fichier d'une vidéo uploadée et en extrait les métadonnées : durée,
dimensions, codecs, conteneur. C'est l'étape qui précède le transcodage.

  ``index`` — `GET /video-probe/{uuid}` : sonde le fichier d'origine de la vidéo
              et renvoie ses métadonnées en JSON.

Nécessite **ffprobe** installé (binaire configuré par ``FORGE_VIDEO_FFPROBE_BIN``).
Réponses pédagogiques : ``404`` si l'UUID est inconnu, ``502`` si la sonde échoue.
"""
from pathlib import Path

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.config import load_video_config
from forge_mvc_video.probe import VideoProbeError, probe_video
from forge_mvc_video.storage.repository import VideoRepository


_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init)."
    ),
}


class VideoProbeController(BaseController):
    """Starter pédagogique : extraire les métadonnées d'une vidéo via ffprobe."""

    @staticmethod
    def index(request: Request) -> Response:
        uuid = request.route("uuid")
        try:
            video = VideoRepository().get_by_uuid(uuid)
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        if video is None:
            return Response.json(
                {"error": "video_not_found", "uuid": uuid}, status=404
            )
        cfg = load_video_config()
        path = str(Path(cfg.storage_root) / video["original_path"])
        try:
            meta = probe_video(path, config=cfg)
        except VideoProbeError as exc:
            return Response.json(
                {"error": "probe_failed", "message": str(exc)}, status=502
            )
        return Response.json({
            "uuid": uuid,
            "metadata": {
                "duration_seconds": meta.duration_seconds,
                "width": meta.width,
                "height": meta.height,
                "video_codec": meta.video_codec,
                "audio_codec": meta.audio_codec,
                "container": meta.container,
            },
        })
