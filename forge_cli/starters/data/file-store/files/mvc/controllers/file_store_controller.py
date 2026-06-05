"""Starter Stocker un document — palier 2 du niveau débutant (progression welcome-files).

Ticket : STARTER-FILE-STORE-001.

La façade **document** de forge-mvc-files : ``save_upload`` valide
(extension/MIME/taille, via le core) puis écrit le fichier et retourne un
``SavedUpload`` décrivant ce qui a été stocké. C'est exactement la primitive que
``forge-mvc-images`` réutilise pour le chemin document (ADR-020).

  ``index`` — `GET  /file-store` : affiche le formulaire (CSRF).
  ``store`` — `POST /file-store` : enregistre le fichier, affiche nom / chemin /
              taille / type ; en cas de refus, montre l'erreur.

Aucune base de données : le fichier est stocké sur le disque.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import UploadError, save_upload


class FileStoreController(BaseController):
    """Starter pédagogique : stocker un document générique."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_store/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def store(request: Request) -> Response:
        uploaded = request.file("document")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_store/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_store/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "file_store/index.html", context=context, request=request
        )
