"""Starter Suivre l'état d'une vidéo — palier 3 du niveau intermédiaire (welcome-video).

Ticket : STARTER-VIDEO-STATUS-001.

Une vidéo suit un **cycle de vie** : ``uploaded`` (téléversée) → ``processing``
(transcodage en cours) → ``ready`` (prête) — ou ``failed`` en cas d'erreur. Ce
palier regroupe les vidéos par statut via ``VideoRepository.list_by_status`` :

  ``index`` — `GET /video-status` : les vidéos rangées par statut, en JSON.

C'est le statut que le worker de transcodage (niveau avancé) fait avancer ;
ici, on l'**observe**. Réponse ``503`` pédagogique si la table manque.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_video.storage.repository import VideoRepository


# Cycle de vie d'une vidéo dans le module Forge Vidéo.
_STATUSES = ("uploaded", "processing", "ready", "failed")

_STORAGE_NOT_READY = {
    "error": "video_storage_not_ready",
    "message": (
        "La table videos n'est pas encore disponible. "
        "Applique la migration Forge Vidéo (forge video:init) avant de "
        "suivre les statuts."
    ),
}


class VideoStatusController(BaseController):
    """Starter pédagogique : observer le cycle de vie des vidéos par statut."""

    @staticmethod
    def index(request: Request) -> Response:
        repo = VideoRepository()
        try:
            by_status = {
                status: repo.list_by_status(status, limit=20)
                for status in _STATUSES
            }
        except Exception:
            return Response.json(_STORAGE_NOT_READY, status=503)
        return Response.json({"by_status": by_status})
