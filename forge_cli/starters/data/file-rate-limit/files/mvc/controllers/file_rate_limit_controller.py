"""Starter Limiter les uploads — palier 2 du niveau intermédiaire (welcome-files).

Ticket : STARTER-FILE-RATE-LIMIT-001.

Une route d'upload publique est une cible : sans garde, on peut la marteler.
``forge-mvc-files`` fournit un **rate-limit par IP** en mémoire (fenêtre
glissante) : ``is_upload_rate_limited(ip)`` dit si l'IP a atteint le quota,
``record_upload_attempt(ip)`` enregistre une tentative.

  ``index``  — `GET  /file-rate-limit` : formulaire (CSRF) + règle affichée.
  ``upload`` — `POST /file-rate-limit` : refuse (``429``) au-delà du quota, sinon
               enregistre la tentative puis stocke le fichier.

Aucune base de données : le compteur vit en mémoire du processus.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_files import (
    UploadError,
    is_upload_rate_limited,
    record_upload_attempt,
    save_upload,
)


class FileRateLimitController(BaseController):
    """Starter pédagogique : protéger une route d'upload par rate-limit."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "file_rate_limit/index.html",
            context={"csrf_token": BaseController.csrf_token(request)},
            request=request,
        )

    @staticmethod
    def upload(request: Request) -> Response:
        context = {"csrf_token": BaseController.csrf_token(request)}
        if is_upload_rate_limited(request.ip):
            context["rate_limited"] = True
            return BaseController.render(
                "file_rate_limit/index.html", context=context, request=request, status=429
            )
        record_upload_attempt(request.ip)
        uploaded = request.file("document")
        if uploaded is None:
            context["error"] = "Aucun fichier sélectionné."
            return BaseController.render(
                "file_rate_limit/index.html", context=context, request=request
            )
        try:
            saved = save_upload(uploaded, "documents")
        except UploadError as exc:
            context["error"] = str(exc)
            return BaseController.render(
                "file_rate_limit/index.html", context=context, request=request
            )
        context["saved"] = saved
        return BaseController.render(
            "file_rate_limit/index.html", context=context, request=request
        )
