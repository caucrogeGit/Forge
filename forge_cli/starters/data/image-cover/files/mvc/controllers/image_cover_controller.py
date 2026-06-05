"""Starter Image de couverture — palier 1 du niveau avancé (welcome-images).

Ticket : STARTER-IMAGE-COVER-001.

Une entité a souvent **une** image mise en avant : sa couverture. Forge la modélise
par le **rôle** ``cover`` (distinct de ``gallery``). ``get_cover_media`` lit cette
couverture, avec repli optionnel sur la première image de la galerie.

  ``index``     — `GET  /image-cover` : affiche la couverture courante.
  ``set_cover`` — `POST /image-cover` : téléverse une image et la rattache en
                  rôle ``cover``.

La table ``media`` est créée par la migration livrée avec le starter
(``forge migration:apply``). Si elle manque, la page reste **pédagogique**.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import attach_media_to_entity, get_cover_media, save_image_upload

_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageCoverController(BaseController):
    """Starter pédagogique : désigner et afficher l'image de couverture."""

    @staticmethod
    def _render(request: Request, **extra) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        context.update(extra)
        if "error" not in context:
            try:
                context["cover"] = get_cover_media(
                    _ENTITY_NAME, _ENTITY_ID, role="cover", fallback_to_gallery=True
                )
            except Exception:
                context["error"] = _TABLE_NOT_READY
        return BaseController.render(
            "image_cover/index.html", context=context, request=request
        )

    @staticmethod
    def index(request: Request) -> Response:
        return ImageCoverController._render(request)

    @staticmethod
    def set_cover(request: Request) -> Response:
        uploaded = request.file("image")
        if uploaded is None:
            return ImageCoverController._render(request, error="Aucune image sélectionnée.")
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            return ImageCoverController._render(request, error=str(exc))
        try:
            attach_media_to_entity(
                saved, entity_name=_ENTITY_NAME, entity_id=_ENTITY_ID, role="cover"
            )
        except Exception:
            return ImageCoverController._render(request, error=_TABLE_NOT_READY)
        return ImageCoverController._render(request, updated="Couverture mise à jour.")
