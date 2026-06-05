"""Starter Téléverser un audio — palier 2 du niveau débutant (progression welcome-audio).

Ticket : STARTER-AUDIO-UPLOAD-001.

``ingest_audio`` valide (extension, taille) et **stocke** le fichier source à un
emplacement **uuid-based** (le nom utilisateur n'apparaît jamais dans le chemin —
anti-traversal par construction). Aucun ``ffprobe``/``ffmpeg`` n'est lancé ici :
le sondage et le transcodage sont des paliers avancés.

  ``index``  — `GET  /audio-upload` : affiche le formulaire (CSRF).
  ``upload`` — `POST /audio-upload` : ingère l'audio, affiche l'uuid attribué, le
               chemin, la taille et le type ; en cas de refus, montre l'erreur.

Aucune base de données : le fichier est stocké sur le disque, repéré par uuid.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_audio import AudioIngestError, ingest_audio


class AudioUploadController(BaseController):
    """Starter pédagogique : ingérer un fichier audio source."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "audio_upload/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("audio")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier audio sélectionné."
            return BaseController.render(
                "audio_upload/index.html", context=context, request=request
            )
        try:
            result = ingest_audio(uploaded.content, uploaded.filename or "audio")
        except AudioIngestError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "audio_upload/index.html", context=context, request=request
            )
        context["result"] = result
        return BaseController.render(
            "audio_upload/index.html", context=context, request=request
        )
