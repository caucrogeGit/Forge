"""Starter Validation serveur — palier 7 de la progression pédagogique.

Ticket : STARTER-SERVER-VALIDATION-001.

Le contrôleur expose deux actions et démontre la contrôle minimum
côté serveur : ne jamais faire confiance au client.

  ``index``  — `GET /server-validation`, rend le formulaire HTML avec
               le token CSRF passé dans le contexte.
  ``submit`` — `POST /server-validation`, lit `name` avec
               `request.form("name", default="").strip()`, refuse les
               valeurs vides avec `Response.text(..., status=422)`,
               sinon retourne `Response.text(f"Bonjour {name}")`.

Pas de framework de formulaire, pas de classe `Validator`, pas de
réaffichage HTML avec messages dynamiques — seulement le contrôle
minimum.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class ServerValidationController(BaseController):
    """Starter pédagogique : valider une donnée côté serveur."""

    @staticmethod
    def index(request: Request) -> Response:
        csrf_token = BaseController.csrf_token(request)
        return BaseController.render(
            "server_validation/index.html",
            context={"csrf_token": csrf_token},
            request=request,
        )

    @staticmethod
    def submit(request: Request) -> Response:
        name = request.form("name", default="").strip()

        if not name:
            return Response.text("Le prénom est obligatoire", status=422)

        return Response.text(f"Bonjour {name}")
