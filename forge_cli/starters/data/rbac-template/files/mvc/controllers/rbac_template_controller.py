"""Starter Permission dans un template — palier 3 du niveau intermédiaire (welcome-rbac).

Ticket : STARTER-RBAC-TEMPLATE-001.

Le RBAC ne sert pas qu'à bloquer une route : il **adapte l'interface**.
``make_can(request)`` retourne un callable ``can(code) -> bool`` lié à la requête.
Forge l'expose automatiquement dans les templates Jinja sous le nom ``can()`` — on
affiche ou masque un bouton selon la permission.

  ``index`` — `GET /rbac-template` : page montrant ``can("article.list")`` et
              ``can("article.create")``.

Aucune base de données. Sans utilisateur connecté, ``can(...)`` renvoie ``False``.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController

from forge_mvc_rbac import make_can


class RbacTemplateController(BaseController):
    """Starter pédagogique : conditionner l'UI à une permission via can()."""

    @staticmethod
    def index(request: Request) -> Response:
        can = make_can(request)
        return BaseController.render(
            "rbac_template/index.html",
            context={"can_list": can("article.list"), "can_create": can("article.create")},
            request=request,
        )
