"""Starter Supprimer proprement — palier 2 du niveau avancé (welcome-images).

Ticket : STARTER-IMAGE-DELETE-001.

Supprimer une image, c'est supprimer **trois choses** : la ligne ``media``, le
fichier original et ses variantes. ``delete_media(..., delete_files=True)`` fait
les trois en une fois, sans laisser de fichier orphelin.

  ``index``  — `GET  /image-delete` : liste les images avec un bouton Supprimer.
  ``delete`` — `POST /image-delete` : supprime ligne + fichiers via ``delete_media``.

La table ``media`` est créée par la migration livrée avec le starter
(``forge migration:apply``). Si elle manque, la page reste **pédagogique**.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import delete_media, list_media_for_entity

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageDeleteController(BaseController):
    """Starter pédagogique : supprimer une image (ligne + fichier + variantes)."""

    @staticmethod
    def _render(request: Request, **extra) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        context.update(extra)
        try:
            context["items"] = list_media_for_entity(
                _ENTITY_NAME, _ENTITY_ID, role="gallery"
            )
        except Exception:
            context["error"] = _TABLE_NOT_READY
        return BaseController.render(
            "image_delete/index.html", context=context, request=request
        )

    @staticmethod
    def index(request: Request) -> Response:
        return ImageDeleteController._render(request)

    @staticmethod
    def delete(request: Request) -> Response:
        media_id = request.form("media_id")
        if not media_id:
            return ImageDeleteController._render(request, error="Aucune image sélectionnée.")
        try:
            delete_media(int(media_id), delete_files=True)
        except Exception:
            return ImageDeleteController._render(request, error=_TABLE_NOT_READY)
        return ImageDeleteController._render(request, updated=f"Image #{media_id} supprimée.")
