"""Starter Garde de sécurité à l'upload — palier 3 du niveau avancé (welcome-images).

Ticket : STARTER-IMAGE-SAFETY-001.

Avant d'écrire quoi que ce soit, ``forge-mvc-images`` vérifie que le fichier reçu
est **vraiment** une image et qu'elle n'est pas démesurée (défense anti-bombe de
décompression). ``verify_image_content`` porte cette garde ; ce palier la **met
en scène** sans rien écrire :

  ``index``   — `GET  /image-safety` : formulaire + politique de sécurité affichée.
  ``check``   — `POST /image-safety` : passe le fichier à ``verify_image_content``
                et indique s'il est accepté ou rejeté (et pourquoi). Aucune écriture.
  ``inspect`` — `GET /image-safety/inspect` : la politique en JSON.

Aucune base de données : c'est un palier de **diagnostic** (images est une brique
bibliothèque, sans CLI ``images:doctor``).
"""
import os

from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError
from forge_mvc_images import ALLOWED_IMAGE_EXTENSIONS, verify_image_content


def _guard_policy() -> dict:
    """Décrit la politique de sécurité appliquée aux uploads d'image."""
    return {
        "allowed_extensions": sorted(ALLOWED_IMAGE_EXTENSIONS),
        "max_image_pixels": int(os.getenv("UPLOAD_MAX_IMAGE_PIXELS", "24000000")),
    }


class ImageSafetyController(BaseController):
    """Starter pédagogique : démontrer la garde de sécurité à l'upload."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "image_safety/index.html",
            context={"csrf_token": BaseController.csrf_token(request), "guard": _guard_policy()},
            request=request,
        )

    @staticmethod
    def check(request: Request) -> Response:
        uploaded = request.file("image")
        context = {"csrf_token": BaseController.csrf_token(request), "guard": _guard_policy()}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render("image_safety/index.html", context=context, request=request)
        try:
            verify_image_content(uploaded.content)
        except UploadError as exc:
            context["rejected"] = str(exc)
            return BaseController.render("image_safety/index.html", context=context, request=request)
        context["accepted"] = uploaded.filename or "image"
        return BaseController.render("image_safety/index.html", context=context, request=request)

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_guard_policy())
