"""Starter Bonjour Forge Images — palier 1 du niveau débutant (progression welcome-images).

Ticket : STARTER-IMAGES-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-images``. Deux routes :

  ``index``   — `GET /images-welcome` : réponse texte « Bonjour Forge Images ».
  ``inspect`` — `GET /images-welcome/inspect` : sérialise en JSON ce que le
                module sait traiter — formats autorisés (``ALLOWED_IMAGE_*``) et
                tailles de variantes générées (``IMAGE_VARIANT_SIZES``).

Aucune base de données : on découvre simplement que le module est installé et
quelles images il accepte. Installez d'abord le module depuis les sources :
``pip install -e packages/forge-mvc-images/`` (dépend de ``forge-mvc-files``).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_images import (
    ALLOWED_IMAGE_EXTENSIONS,
    ALLOWED_IMAGE_MIME_TYPES,
    IMAGE_VARIANT_SIZES,
)


def _capabilities() -> dict:
    """Décrit ce que forge-mvc-images sait accepter et produire."""
    return {
        "allowed_extensions": sorted(ALLOWED_IMAGE_EXTENSIONS),
        "allowed_mime_types": sorted(ALLOWED_IMAGE_MIME_TYPES),
        "variant_sizes": {
            name: list(size) for name, size in IMAGE_VARIANT_SIZES.items()
        },
    }


class ImagesWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Images."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Images")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_capabilities())
