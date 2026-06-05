"""Starter Supprimer un fichier — palier 3 du niveau intermédiaire (welcome-files).

Ticket : STARTER-FILE-DELETE-001.

``delete_media_file`` supprime un fichier stocké à partir de son **chemin
relatif**, en restant **à l'intérieur** de la racine d'upload (anti-traversal :
un chemin qui tente d'en sortir est refusé). Elle retourne un compte rendu de ce
qui a été supprimé.

  ``index``  — `GET  /file-delete` : formulaire (CSRF) + champ chemin.
  ``delete`` — `POST /file-delete` : supprime le fichier et confirme.

Aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import delete_media_file


class FileDeleteController(BaseController):
    """Starter pédagogique : supprimer un fichier stocké, sans faille de chemin."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_delete/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def delete(request: Request) -> Response:
        path = request.form("path")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if not path:
            context["error"] = "Indiquez le chemin du fichier à supprimer."
            return BaseController.render(
                "file_delete/index.html", context=context, request=request
            )
        try:
            result = delete_media_file(path)
        except Exception:
            context["error"] = "Chemin invalide ou hors de la racine d'upload."
            return BaseController.render(
                "file_delete/index.html", context=context, request=request
            )
        if result.get("original"):
            context["deleted"] = path
        else:
            context["not_found"] = path
        return BaseController.render(
            "file_delete/index.html", context=context, request=request
        )
