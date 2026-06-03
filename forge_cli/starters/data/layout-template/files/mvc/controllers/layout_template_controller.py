"""Starter Héritage de gabarit — palier 4 du niveau intermédiaire.

Ticket : STARTER-LAYOUT-TEMPLATE-001.

Jusqu'ici, chaque vue était un **document HTML complet** dupliqué. Ici on
factorise l'enveloppe commune (``<head>``, en-tête, pied) dans un **gabarit**
``layouts/starter_layout.html`` ; la page n'en garde que son contenu propre via
``{% extends %}`` + ``{% block %}``.

  ``index`` — `GET /layout-template`, rend ``layout_template/index.html`` qui
              hérite du gabarit partagé.

Aucune base de données, aucune écriture, aucun formulaire.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class LayoutTemplateController(BaseController):
    """Starter pédagogique : héritage de gabarit Jinja."""

    @staticmethod
    def index(request: Request) -> Response:
        return BaseController.render(
            "layout_template/index.html",
            context={"titre": "Héritage de gabarit"},
            request=request,
        )
