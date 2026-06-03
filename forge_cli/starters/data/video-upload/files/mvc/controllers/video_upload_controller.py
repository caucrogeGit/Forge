"""Starter Téléverser une vidéo — palier 1 du niveau intermédiaire (welcome-video).

Ticket : STARTER-VIDEO-UPLOAD-001.

On **alimente** le module : un formulaire envoie un fichier vidéo. ``ingest_video``
le **valide** (taille, conteneur déclaré), le **stocke** sous un UUID (jamais le
nom de fichier utilisateur) et **insère** une ligne ``videos`` au statut
``uploaded`` — le tout **sans ffmpeg**. Le transcodage est un worker séparé
(``forge video:process``, niveau avancé) : jamais pendant une requête HTTP.

  ``index``  — `GET  /video-upload` : formulaire + liste des vidéos.
  ``upload`` — `POST /video-upload` : ingère le fichier reçu, puis redirige.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.ingest import VideoIngestError, ingest_video
from forge_mvc_video.storage.repository import VideoRepository


class VideoUploadController(BaseController):
    """Starter pédagogique : ingérer une vidéo uploadée (statut uploaded)."""

    @staticmethod
    def index(request: Request) -> Response:
        return VideoUploadController._page(request)

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("video")
        if uploaded is None:
            return VideoUploadController._page(
                request, error="Aucun fichier sélectionné."
            )
        title = (request.form("title") or "").strip() or None
        try:
            ingest_video(uploaded.read(), uploaded.filename, title=title)
        except VideoIngestError as exc:
            return VideoUploadController._page(request, error=str(exc))
        return BaseController.redirect("/video-upload")

    @staticmethod
    def _page(request: Request, error: str | None = None) -> Response:
        try:
            videos = VideoRepository().list_recent(limit=20)
        except Exception:
            videos = []
        context = {
            "videos": videos,
            "csrf_token": BaseController.csrf_token(request),
        }
        if error:
            context["error"] = error
        return BaseController.render(
            "video_upload/index.html", context=context, request=request
        )
