"""Starter Transcoder une vidéo — palier 2 du niveau avancé (welcome-video).

Ticket : STARTER-VIDEO-TRANSCODE-001.

Le **vrai transcodage**. ``forge video:process`` lance un **worker** qui, pour une
vidéo ``uploaded``, sonde la source, génère un poster et transcode en MP4 via
**ffmpeg** (``process_video``), faisant avancer le statut :

    uploaded → processing → ready   (ou failed)

Le transcodage est lourd : il reste un **worker CLI**, jamais une requête HTTP.
Cette route ne transcode donc pas — elle **liste les vidéos en attente** et la
config ffmpeg, pour préparer le lancement de ``forge video:process``.

  ``index`` — `GET /video-transcode` : vidéos `uploaded` à traiter + config ffmpeg.

ffmpeg requis pour le traitement réel.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.config import load_video_config
from forge_mvc_video.storage.repository import VideoRepository


class VideoTranscodeController(BaseController):
    """Starter pédagogique : préparer le worker de transcodage (sans bloquer le web)."""

    @staticmethod
    def index(request: Request) -> Response:
        cfg = load_video_config()
        try:
            pending = VideoRepository().list_by_status("uploaded", limit=50)
        except Exception:
            pending = []
        return BaseController.render(
            "video_transcode/index.html",
            context={"ffmpeg_bin": cfg.ffmpeg_bin, "pending": pending},
            request=request,
        )
