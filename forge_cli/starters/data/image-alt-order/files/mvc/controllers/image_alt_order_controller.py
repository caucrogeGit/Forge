"""Starter Texte alternatif et ordre — palier 3 du niveau intermédiaire (welcome-images).

Ticket : STARTER-IMAGE-ALT-ORDER-001.

Une galerie utile est **accessible** et **ordonnée**. Ce palier édite deux champs
d'une ligne ``media`` : le texte alternatif (``alt_text``, lu par les lecteurs
d'écran) et la position d'affichage (``position``).

  ``index``  — `GET  /image-alt-order` : liste les images de l'entité de démo
               avec un formulaire d'édition par image.
  ``update`` — `POST /image-alt-order` : applique ``update_media_alt_text`` et
               ``update_media_position`` sur l'image choisie.

La table ``media`` est créée par la migration livrée avec le starter
(``forge migration:apply``). Si elle manque, la page reste **pédagogique**.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import (
    list_media_for_entity,
    update_media_alt_text,
    update_media_position,
)

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageAltOrderController(BaseController):
    """Starter pédagogique : éditer accessibilité et ordre des médias."""

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
            "image_alt_order/index.html", context=context, request=request
        )

    @staticmethod
    def index(request: Request) -> Response:
        return ImageAltOrderController._render(request)

    @staticmethod
    def update(request: Request) -> Response:
        media_id = request.form("media_id")
        alt_text = request.form("alt_text")
        position = request.form("position")
        if not media_id:
            return ImageAltOrderController._render(
                request, error="Aucune image sélectionnée."
            )
        try:
            update_media_alt_text(int(media_id), alt_text or None)
            update_media_position(int(media_id), int(position or 0))
        except Exception:
            return ImageAltOrderController._render(request, error=_TABLE_NOT_READY)
        return ImageAltOrderController._render(
            request, updated=f"Image #{media_id} mise à jour."
        )
