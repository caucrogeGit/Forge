"""Starter Valider un upload — palier 1 du niveau intermédiaire (welcome-files).

Ticket : STARTER-FILE-VALIDATE-001.

Avant d'écrire, ``save_upload`` **valide** : extension, type MIME, taille. Chaque
refus lève une exception **précise** de la hiérarchie ``UploadError`` (qui vit
dans le core et est réexportée par files — ADR-019). Ce palier expose cette
**taxonomie** pour qu'on sache exactement pourquoi un fichier est rejeté.

  ``index`` — `GET  /file-validate` : formulaire (CSRF) + politique affichée.
  ``check`` — `POST /file-validate` : tente l'upload et nomme la règle qui rejette.

Aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import (
    UploadError,
    UploadInvalidExtensionError,
    UploadInvalidMimeTypeError,
    UploadTooLargeError,
    save_upload,
)


class FileValidateController(BaseController):
    """Starter pédagogique : comprendre la taxonomie des refus d'upload."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_validate/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def check(request: Request) -> Response:
        uploaded = request.file("document")
        context = {"csrf_token": BaseController.csrf_token(request)}
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_validate/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadInvalidExtensionError as exc:
            context["rejected"] = {"rule": "extension", "message": str(exc)}
        except UploadInvalidMimeTypeError as exc:
            context["rejected"] = {"rule": "type MIME", "message": str(exc)}
        except UploadTooLargeError as exc:
            context["rejected"] = {"rule": "taille", "message": str(exc)}
        except UploadError as exc:
            context["rejected"] = {"rule": "autre", "message": str(exc)}
        else:
            context["accepted"] = saved.original_name
        return BaseController.render(
            "file_validate/index.html", context=context, request=request
        )
