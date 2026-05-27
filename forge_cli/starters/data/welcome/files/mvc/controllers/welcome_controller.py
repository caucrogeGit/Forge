"""Starter Bonjour Forge — premier contact minimal avec le framework.

Ticket : STARTER-BONJOUR-FORGE-MINIMAL-001.

Le contrôleur expose le chemin le plus court entre une requête HTTP et
une réponse texte :

  1. ``index`` — `Response.text("Bonjour Forge")` : texte brut.
  2. ``greet`` — lecture d'un paramètre via `request.param(...)`.

Aucune vue HTML, aucune base de données, aucun moteur Jinja2.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):

    @staticmethod
    def index(request: Request) -> Response:
        return Response.text("Bonjour Forge")

    @staticmethod
    def greet(request: Request) -> Response:
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")
