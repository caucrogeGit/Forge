"""Starter Le détail d'une vidéo — palier 3 du niveau débutant (welcome-video).

Ticket : STARTER-VIDEO-DETAIL-001.

Après la liste, on **cible une vidéo précise** par son UUID :

  ``index`` — `GET /video-detail/{uuid}` : la vidéo via ``get_by_uuid``.

Réponses pédagogiques : ``404`` si l'UUID est inconnu, ``503`` si la table
``videos`` n'existe pas encore. Lecture seule, aucun ffmpeg.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.storage.repository import VideoRepository


_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init) avant de lire "
        "une vidéo."
    ),
}


class VideoDetailController(BaseController):
    """Starter pédagogique : lire le détail d'une vidéo par son UUID."""

    @staticmethod
    def index(request: Request) -> Response:
        uuid = request.route_param("uuid")
        try:
            video = VideoRepository().get_by_uuid(uuid)
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        if video is None:
            return Response.json(
                {"error": "video_not_found", "uuid": uuid}, status=404
            )
        return Response.json({"video": video})
