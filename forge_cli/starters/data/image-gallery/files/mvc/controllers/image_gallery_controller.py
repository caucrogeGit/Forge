"""Starter Afficher la galerie — palier 2 du niveau intermédiaire (welcome-images).

Ticket : STARTER-IMAGE-GALLERY-001.

Une fois des images rattachées à une entité (palier précédent), on veut les
**afficher ensemble**. ``get_media_gallery`` lit les médias de rôle ``gallery``
d'une entité et renvoie, pour chacun, l'URL de l'original **et** celles de ses
variantes (``medium``, ``thumbnail``) — prêtes à poser dans des balises `<img>`.

  ``index`` — `GET /image-gallery` : affiche la galerie de l'entité de démo.

La table ``media`` est créée par la migration livrée avec le starter
(``forge migration:apply``). Si elle manque, la page reste **pédagogique**.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import get_media_gallery

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageGalleryController(BaseController):
    """Starter pédagogique : afficher la galerie d'images d'une entité."""

    @staticmethod
    def index(request: Request) -> Response:
        try:
            items = get_media_gallery(_ENTITY_NAME, _ENTITY_ID, role="gallery")
        except Exception:
            return BaseController.render(
                "image_gallery/index.html",
                context={"error": _TABLE_NOT_READY},
                request=request,
            )
        return BaseController.render(
            "image_gallery/index.html",
            context={"items": items},
            request=request,
        )
