"""Starter Téléverser un fichier — palier 2 du niveau avancé.

Ticket : STARTER-FILE-UPLOAD-001.

Recevoir un fichier de l'utilisateur est un classique des applications web. Le
formulaire est en ``multipart/form-data`` ; le contrôleur récupère le fichier
avec ``request.file(...)`` puis le confie à ``core.uploads.save_upload``, qui
**valide** (extension, type MIME, taille) avant d'écrire sur le disque. Forge ne
fait jamais confiance aveuglément au fichier reçu.

  ``index``  — `GET  /file-upload` : affiche le formulaire d'upload (CSRF).
  ``upload`` — `POST /file-upload` : enregistre le fichier reçu et affiche son
               nom et sa taille ; en cas de fichier refusé, montre l'erreur.

Aucune base de données : le fichier est stocké sur le disque, pas en base.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController
from core.uploads import UploadError, save_upload


class FileUploadController(BaseController):
    """Starter pédagogique : recevoir et stocker un fichier uploadé."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_upload/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        uploaded = request.file("document")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_upload/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_upload/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "file_upload/index.html", context=context, request=request
        )
