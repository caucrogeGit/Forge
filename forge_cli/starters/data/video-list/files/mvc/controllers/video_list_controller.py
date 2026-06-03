"""Starter Lister les vidéos — palier 2 du niveau débutant (welcome-video).

Ticket : STARTER-VIDEO-LIST-001.

Le module Forge Vidéo enregistre chaque vidéo (métadonnées + statut) dans la
table ``videos``. Ce palier les **liste** via ``VideoRepository.list_recent`` et
les renvoie en JSON.

  ``index`` — `GET /video-list` : dernières vidéos, ordre du plus récent.

Le starter reste **pédagogique** quand la table n'existe pas encore (aucun
``video:init`` lancé) : au lieu de planter, il renvoie une réponse ``503`` claire.
Aucun ffmpeg, aucune écriture.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.storage.repository import VideoRepository


_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init) avant de "
        "lister les vidéos."
    ),
}


class VideoListController(BaseController):
    """Starter pédagogique : lister les dernières vidéos enregistrées."""

    @staticmethod
    def index(request: Request) -> Response:
        try:
            videos = VideoRepository().list_recent(limit=20)
        except Exception:
            # Table absente, base inaccessible… — on reste pédagogique.
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"videos": videos})
