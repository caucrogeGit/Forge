"""Starter Bonjour Forge Files — palier 1 du niveau débutant (progression welcome-files).

Ticket : STARTER-FILES-WELCOME-001.

Premier contact avec le module **opt-in** ``forge-mvc-files`` : le pipeline
d'**upload générique** extrait du core (ADR-019). C'est la **fondation** sur
laquelle ``forge-mvc-images`` est bâti ; ce parcours en montre la façade
``save_upload`` (documents) puis, au niveau avancé, les **primitives** que les
opt-ins média composent (ADR-020).

  ``index``   — `GET /files-welcome` : réponse texte « Bonjour Forge Files ».
  ``inspect`` — `GET /files-welcome/inspect` : racine de stockage + politique
                d'upload (extensions, MIME, taille max) en JSON.

Aucune base de données. Installe d'abord le module depuis les sources :
``pip install -e packages/forge-mvc-files/``.
"""
from core.forge import get as get_config
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import upload_root


def _capabilities() -> dict:
    """Décrit où et quoi forge-mvc-files accepte de stocker."""
    return {
        "upload_root": str(upload_root()),
        "allowed_extensions": sorted(get_config("upload_allowed_extensions")),
        "allowed_mime_types": sorted(get_config("upload_allowed_mime_types")),
        "max_size_bytes": int(get_config("upload_max_size")),
    }


class FilesWelcomeController(BaseController):
    """Starter pédagogique : premier contact avec Forge Files."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge Files")

    @staticmethod
    def inspect(request: Request) -> Response:
        return Response.json(_capabilities())
