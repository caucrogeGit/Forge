"""Starter Route dynamique — palier 4 de la progression pédagogique.

Ticket : STARTER-DYNAMIC-ROUTE-001.

Le contrôleur expose une route avec un segment variable
(`/dynamic-route/articles/{id}`) et apprend à lire ce segment via
``request.route_param(key, default=...)``.

  ``show`` — lit ``{id}`` et retourne ``Article {id}`` en texte brut.

Aucune vue HTML, aucune base de données, aucun formulaire.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class DynamicRouteController(BaseController):
    """Starter pédagogique : lire un paramètre de route."""

    @staticmethod
    def show(request: Request) -> Response:
        article_id = request.route_param("id", default="inconnu")
        return Response.text(f"Article {article_id}")
