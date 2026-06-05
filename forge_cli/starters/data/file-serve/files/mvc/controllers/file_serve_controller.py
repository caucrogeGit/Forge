"""Starter Servir un fichier — palier 3 du niveau débutant (progression welcome-files).

Ticket : STARTER-FILE-SERVE-001.

Stocker ne sert à rien si on ne peut pas **relire**. ``serve_media_file`` renvoie
un fichier à partir de son **chemin relatif** à la racine d'upload, en garantissant
qu'on ne sort **jamais** de cette racine (anti-traversal), et en répondant ``404``
si le fichier est absent ou le chemin invalide.

  ``index``    — `GET /file-serve` : page d'explication + champ pour un chemin.
  ``download`` — `GET /file-serve/download?path=...` : renvoie le fichier (ou 404).

Aucune base de données : on relit ce qui a été stocké au palier précédent.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import serve_media_file


class FileServeController(BaseController):
    """Starter pédagogique : servir un fichier stocké, sans faille de chemin."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_serve/index.html", context={}, request=request
        )

    @staticmethod
    def download(request: Request) -> Response:
        path = request.param("path") or ""
        if not path:
            return Response.text("Paramètre « path » requis.", status=400)
        # serve_media_file gère lui-même l'anti-traversal et le 404.
        return serve_media_file(path)
