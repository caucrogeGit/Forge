"""Starter Paramètres d'URL — palier 2 de la progression pédagogique.

Ticket : STARTER-QUERY-PARAMS-001.

Le contrôleur expose deux routes qui apprennent à lire une valeur passée
dans l'URL via ``request.param(key, default=...)`` :

  1. ``index`` — texte explicatif indiquant quoi tester.
  2. ``hello`` — lit ``?name=...`` et retourne ``Bonjour {name}``.

Aucune vue HTML, aucune base de données, aucun moteur Jinja2.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class QueryParamsController(BaseController):
    """Starter pédagogique : lire des paramètres d'URL."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text(
            "Ajoutez ?name=Roger à l'URL, puis ouvrez /query-params/hello?name=Roger"
        )

    @staticmethod
    def hello(request: Request) -> Response:
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")
