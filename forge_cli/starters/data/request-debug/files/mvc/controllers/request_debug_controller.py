"""Starter Inspecter une requête — palier 5 de la progression pédagogique.

Ticket : STARTER-REQUEST-DEBUG-001.

Le contrôleur expose une route qui apprend à explorer la requête
courante : ``request.data`` (vue inspectable, secrets masqués) rendue
par ``Response.debug(...)`` (HTML pédagogique en ``APP_ENV=dev``,
404 en ``APP_ENV=prod``).

  ``index`` — retourne ``Response.debug(request.data)``.

Aucune vue HTML livrée, aucune base de données, aucun formulaire.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class RequestDebugController(BaseController):
    """Starter pédagogique : inspecter une requête en développement."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.debug(request.data)
