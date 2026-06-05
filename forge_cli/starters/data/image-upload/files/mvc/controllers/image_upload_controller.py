"""Starter Téléverser une image — palier 2 du niveau débutant (progression welcome-images).

Ticket : STARTER-IMAGE-UPLOAD-001.

L'upload d'image n'est pas un upload de fichier comme un autre. Le formulaire est
en ``multipart/form-data`` ; le contrôleur récupère l'image avec
``request.file(...)`` puis la confie à ``forge_mvc_images.save_image_upload``,
qui — contrairement à l'upload brut de ``forge-mvc-files`` :

  1. **vérifie que le contenu est une vraie image** avant toute écriture
     (``verify_image_content`` : un PDF/script déguisé en ``.jpg`` est rejeté,
     garde anti-bombe de décompression incluse) ;
  2. écrit le fichier ;
  3. **génère les variantes** ``medium`` et ``thumbnail``.

  ``index``  — `GET  /image-upload` : affiche le formulaire (CSRF).
  ``upload`` — `POST /image-upload` : enregistre l'image, affiche son nom, sa
               taille et les variantes générées ; en cas de refus, montre l'erreur.

Aucune base de données : l'image et ses variantes sont stockées sur le disque.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import save_image_upload


class ImageUploadController(BaseController):
    """Starter pédagogique : recevoir, vérifier et décliner une image en variantes."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "image_upload/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucune image sélectionnée."
            return BaseController.render(
                "image_upload/index.html", context=context, request=request
            )
        try:
            saved = save_image_upload(uploaded, "images")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "image_upload/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "image_upload/index.html", context=context, request=request
        )
