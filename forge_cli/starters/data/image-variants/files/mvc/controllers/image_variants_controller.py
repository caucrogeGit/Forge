"""Starter Miniatures et variantes — palier 3 du niveau débutant (progression welcome-images).

Ticket : STARTER-IMAGE-VARIANTS-001.

Quand on téléverse une image, ``forge-mvc-images`` génère deux déclinaisons en
plus de l'originale : ``medium`` et ``thumbnail`` (voir ``IMAGE_VARIANT_SIZES``).
Ce palier explique **où vivent ces variantes** et **comment construire leurs
URL**, sans rien téléverser :

  ``image_variant_relative_paths(path)`` dérive — par simple transformation de
  chemin — l'originale et ses variantes (``parent/medium/nom`` et
  ``parent/thumbnail/nom``). ``media_url(rel)`` en fait une URL publique
  ``/media/...``.

  ``index``   — `GET /image-variants` : affiche, pour un chemin d'image donné
                (paramètre ``?path=``), l'originale et ses variantes avec leurs URL.
  ``inspect`` — `GET /image-variants/inspect` : la même information en JSON.

Aucune écriture, aucune base de données : c'est une transformation de chaîne pure,
utile pour comprendre la convention de nommage des variantes.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import (
    IMAGE_VARIANT_SIZES,
    image_variant_relative_paths,
    media_url,
)

# Chemin d'exemple : aucune image réelle n'est requise, on illustre la convention.
_DEMO_PATH = "images/2026/photo.jpg"


def _variants_view(path: str) -> dict:
    """Décrit l'originale et ses variantes (chemin relatif + URL publique)."""
    relative = image_variant_relative_paths(path)
    return {
        "path": path,
        "sizes": {name: list(size) for name, size in IMAGE_VARIANT_SIZES.items()},
        "variants": {
            name: {"relative_path": rel, "url": media_url(rel)}
            for name, rel in relative.items()
        },
    }


class ImageVariantsController(BaseController):
    """Starter pédagogique : comprendre la dérivation des variantes d'image."""

    @staticmethod
    def index(request: Request) -> Response:
        path = request.param("path") or _DEMO_PATH
        return BaseController.render(
            "image_variants/index.html",
            context=_variants_view(path),
            request=request,
        )

    @staticmethod
    def inspect(request: Request) -> Response:
        path = request.param("path") or _DEMO_PATH
        return Response.json(_variants_view(path))
