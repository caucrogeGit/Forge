"""Starter Premier formulaire POST — palier 6 de la progression pédagogique.

Ticket : STARTER-FORM-POST-001.

Le contrôleur expose deux actions :

  ``index``  — `GET /form-post`, rend le formulaire HTML avec le
                 token CSRF passé dans le contexte.
  ``submit`` — `POST /form-post`, lit le champ `name` avec
                 `request.form("name", default="Forge")` et retourne
                 `Response.text(f"Bonjour {name}")`.

CSRF activé par défaut (`router.group(..., csrf=True)`) — le token
est généré via ``BaseController.csrf_token(request)`` et vérifié
automatiquement par le middleware Forge sur la requête POST.

Aucune validation serveur avancée, aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class FormPostController(BaseController):
    """Starter pédagogique : envoyer un premier formulaire POST."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "form_post/index.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )

    @staticmethod
    def submit(request: Request) -> Response:
        name = request.form("name", default="Forge")
        return Response.text(f"Bonjour {name}")
