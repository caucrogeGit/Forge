"""Starter Réponse JSON — palier de la progression pédagogique.

Ticket : STARTER-JSON-RESPONSE-001.

Le contrôleur expose une route qui retourne des données structurées au
format JSON plutôt qu'un texte ou une page HTML :

  ``index`` — `GET /json-response`, retourne `Response.json({...})`
              (en-tête `Content-Type: application/json`).

Aucune vue HTML, aucune base de données, aucun formulaire. C'est la
brique de base d'une API JSON (consommée par un front, un script ou
Forge Design).
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class JsonResponseController(BaseController):
    """Starter pédagogique : retourner une réponse JSON."""

    @staticmethod
    def index(request: Request) -> Response:
        return Response.json(
            {
                "framework": "Forge",
                "message": "Bonjour JSON",
                "items": ["alpha", "beta", "gamma"],
            }
        )
