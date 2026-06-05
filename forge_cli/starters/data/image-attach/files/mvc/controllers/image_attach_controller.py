"""Starter Rattacher une image à une entité — palier 1 du niveau intermédiaire (welcome-images).

Ticket : STARTER-IMAGE-ATTACH-001.

Jusqu'ici l'image vivait seulement sur le disque. Ce palier introduit la
**couche médias en base** : après l'upload, on crée une ligne ``media`` reliée à
une entité, avec ``attach_media_to_entity``. On découvre ainsi qu'une image
appartient à « quelque chose » (ici une entité de démo neutre).

  ``index``  — `GET  /image-attach` : affiche le formulaire (CSRF).
  ``attach`` — `POST /image-attach` : téléverse l'image puis crée sa ligne
               ``media`` (rôle ``gallery``), affiche l'identifiant attribué.

La table ``media`` est créée par la **migration livrée avec le starter** ;
applique-la avec ``forge migration:apply``. Si la table manque, la route reste
**pédagogique** (réponse explicite) plutôt que de planter.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import attach_media_to_entity, save_image_upload

# Entité de démo neutre : la table `media` n'impose aucune clé étrangère, on
# illustre le rattachement sans dépendre d'une entité métier réelle.
_ENTITY_NAME = "gallery-demo"
_ENTITY_ID = 1

_TABLE_NOT_READY = (
    "La table media n'est pas encore disponible. Applique la migration livrée "
    "avec le starter : forge migration:apply."
)


class ImageAttachController(BaseController):
    """Starter pédagogique : relier une image uploadée à une entité en base."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "image_attach/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def attach(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucune image sélectionnée."
            return BaseController.render(
                "image_attach/index.html", context=context, request=request
            )
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "image_attach/index.html", context=context, request=request
            )
        try:
            media_id = attach_media_to_entity(
                saved,
                entity_name=_ENTITY_NAME,
                entity_id=_ENTITY_ID,
                role="gallery",
            )
        except Exception:
            # Table absente, base inaccessible… — on reste pédagogique.
            context["error"] = _TABLE_NOT_READY
            return BaseController.render(
                "image_attach/index.html", context=context, request=request
            )
        context["saved"] = saved
        context["media_id"] = media_id
        return BaseController.render(
            "image_attach/index.html", context=context, request=request
        )
