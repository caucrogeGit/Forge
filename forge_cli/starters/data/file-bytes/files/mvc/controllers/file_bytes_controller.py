"""Starter Écrire des octets générés — palier 3 du niveau avancé (welcome-files).

Ticket : STARTER-FILE-BYTES-001.

Tout n'arrive pas par un upload HTTP : parfois le serveur **produit** lui-même un
fichier (rapport, export CSV, PDF généré). ``save_bytes`` est la primitive d'écriture
sûre — elle range des octets dans la zone d'upload avec un nom sûr, anti-traversal.
C'est la brique bas niveau sur laquelle ``save_upload`` lui-même est bâti (ADR-020).

  ``index``    — `GET  /file-bytes` : formulaire (CSRF) pour saisir un contenu.
  ``generate`` — `POST /file-bytes` : écrit le contenu via ``save_bytes`` et montre
                 le fichier créé.

Aucune base de données ; aucun upload : le contenu est généré côté serveur.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import save_bytes, upload_root


class FileBytesController(BaseController):
    """Starter pédagogique : écrire un fichier généré côté serveur."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_bytes/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def generate(request: Request) -> Response:
        content = request.form("content") or "Fichier généré par Forge."
        context = {"csrf_token": BaseController.csrf_token(request)}
        try:
            path = save_bytes(
                content.encode("utf-8"),
                original_name="rapport.txt",
                category="documents",
                root=upload_root(),
            )
        except Exception as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_bytes/index.html", context=context, request=request
            )
        context["generated_name"] = path.name
        return BaseController.render(
            "file_bytes/index.html", context=context, request=request
        )
