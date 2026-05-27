"""Starter Première vue HTML — palier 3 de la progression pédagogique.

Ticket : STARTER-FIRST-HTML-VIEW-001.

Le contrôleur expose une seule route qui apprend à rendre une vue HTML
via ``BaseController.render(...)`` (au lieu de ``Response.text(...)``
utilisé aux paliers précédents).

  ``index`` — rend ``mvc/views/first_html_view/index.html``.

Aucune base de données, aucun formulaire, aucune route dynamique.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class FirstHtmlViewController(BaseController):
    """Starter pédagogique : rendre une première vue HTML."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render("first_html_view/index.html", request=request)
