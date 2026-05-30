"""Starter Le jeton CSRF — palier de la progression pédagogique.

Ticket : STARTER-CSRF-001.

  ``index`` — `GET /csrf`, rend un formulaire dont le champ caché
              ``csrf_token`` porte le jeton généré par
              ``BaseController.csrf_token(request)``.

Objectif **pédagogique** : comprendre le jeton CSRF (pourquoi il existe,
comment Forge le génère et le vérifie) AVANT de traiter un POST. Le
traitement de la soumission est l'objet du palier suivant
(``form-post``).

Aucune base de données.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class CsrfController(BaseController):
    """Starter pédagogique : comprendre le jeton CSRF."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "csrf/index.html",
            request=request,
            context={"csrf_token": BaseController.csrf_token(request)},
        )
