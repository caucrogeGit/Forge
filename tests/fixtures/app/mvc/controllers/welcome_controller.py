"""Starter Bonjour Forge — premier contact minimal avec le framework.

Ticket : STARTER-BONJOUR-FORGE-MINIMAL-001.

Le contrôleur expose le chemin le plus court entre une requête HTTP et
une réponse texte :

  ``index`` — `Response.text("Bonjour Forge")` : texte brut.

Aucune vue HTML, aucune base de données, aucun moteur Jinja2. La lecture
d'un paramètre d'URL est introduite au palier suivant, le starter
``query-params``.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")
