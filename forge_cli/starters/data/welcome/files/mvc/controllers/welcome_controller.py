"""Starter Bonjour Forge — premier contact avec le framework.

Ticket : STARTER-BONJOUR-FORGE-001.

Le contrôleur introduit progressivement le cycle HTTP de Forge :

  1. ``index``           — `Response.text("Bonjour Forge")` : texte brut.
  2. ``greet``           — lecture d'un paramètre via `request.param(...)`.
  3. ``inspect``         — inspection de la requête via `Response.debug(request.data)`.
  4. ``cycle``           — première vue HTML rendue par `BaseController.render(...)`.
  5. ``request_example`` — vue qui affiche `request.method`, `path`, `params`.
  6. ``response_example`` — vue qui montre la distinction Response HTML vs JSON.
  7. ``routing_example`` — vue qui détaille `mvc/routes.py`.
  8. ``not_found_demo``  — vue qui montre le comportement 404.

Le but est que le développeur voie d'abord *Bonjour Forge* sans aucun
template, puis comprenne progressivement comment Forge rend une vue
HTML — sans recevoir l'intégralité du moteur Jinja2 dès le premier
contact.
"""
from core.http.request import Request
from core.http.response import Response
from core.mvc.controller.base_controller import BaseController


class WelcomeController(BaseController):
    """Cycle HTTP illustré — starter d'entrée Forge sans base de données."""

    # ── Étape 1 — Texte brut ────────────────────────────────────────────────

    @staticmethod
    def index(request: Request) -> Response:
        """`GET /welcome` — premier contact : retourne « Bonjour Forge »
        en `text/plain`, sans aucun template, pour montrer le chemin le
        plus court possible entre une requête et une réponse."""
        return Response.text("Bonjour Forge")

    # ── Étape 2 — Lire un paramètre d'URL ───────────────────────────────────

    @staticmethod
    def greet(request: Request) -> Response:
        """`GET /welcome/greet?name=Roger` — démontre `request.param(...)`."""
        name = request.param("name", default="Forge")
        return Response.text(f"Bonjour {name}")

    # ── Étape 3 — Inspecter la requête ──────────────────────────────────────

    @staticmethod
    def inspect(request: Request) -> Response:
        """`GET /welcome/inspect` — démontre `Response.debug(request.data)`.

        En `APP_ENV=dev`, Forge affiche un dump JSON masqué de la requête.
        En `APP_ENV=prod`, la même méthode refuse et retourne un 404 court
        (voir `Response.debug` dans `docs/reference/http.md`)."""
        return Response.debug(request.data)

    # ── Étape 4 — Première vue HTML ─────────────────────────────────────────

    @staticmethod
    def cycle(request: Request) -> Response:
        """`GET /welcome/cycle` — première utilisation de `render(...)` :
        Forge cherche `mvc/views/welcome/cycle.html` et le rend en HTML."""
        return BaseController.render("welcome/cycle.html", request=request)

    @staticmethod
    def request_example(request: Request) -> Response:
        ctx = {
            "method": request.method,
            "path": request.path,
            "params": {k: v[0] if len(v) == 1 else v for k, v in request.params.items()},
        }
        return BaseController.render("welcome/request_example.html", context=ctx, request=request)

    @staticmethod
    def response_example(request: Request) -> Response:
        return BaseController.render("welcome/response_example.html", request=request)

    @staticmethod
    def routing_example(request: Request) -> Response:
        return BaseController.render("welcome/routing_example.html", request=request)

    @staticmethod
    def not_found_demo(request: Request) -> Response:
        return BaseController.render("welcome/not_found_demo.html", request=request)
