# pyright: strict
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.app.api_routes_loader import load_api_routes as _load_api_routes
from core.database.errors import DatabaseUnavailableError
from core.http.helpers import html as _html
from core.http.router import Router
from core.errors.runtime_error_logger import (
    build_dev_error_context as _dev_error_context,
    log_runtime_error as _log_runtime_error,
)
from core.security.middleware import AuthMiddleware, CsrfMiddleware

if TYPE_CHECKING:
    from core.http.request import Request
    from core.http.response import Response

logger = logging.getLogger(__name__)


def _service_unavailable() -> Response:
    """Réponse 503, sans dépendre d'un gabarit que le projet n'a peut-être pas.

    `errors/503.html` est livré par le squelette, mais Forge n'écrit jamais
    dans un projet existant (principe 9) : une application créée avant cette
    page ne l'a pas. Faire échouer le rendu la ferait retomber en 500, soit
    exactement le message trompeur que ce 503 corrige.

    Le repli est volontairement minimal, en texte brut : à ce stade la base est
    saturée, ce n'est pas le moment de solliciter davantage le serveur.
    """
    from core.http.response import Response

    try:
        rendue = _html("errors/503.html", 503)
    except Exception:  # noqa: BLE001 - moteur de rendu indisponible
        rendue = None
    if rendue is not None and rendue.status == 503:
        return rendue

    # `_html` ne lève pas quand le gabarit manque : il **rend une 500**, ce qui
    # écraserait le code que l'on vient de choisir. On teste donc le statut
    # obtenu, pas la levée d'une exception.
    return Response(
            status=503,
            body=(
                "Service momentanement indisponible.\n"
                "Le service recoit plus de demandes qu'il ne peut en traiter ; "
                "reessayez dans quelques instants.\n"
            ).encode("utf-8"),
            content_type="text/plain; charset=utf-8",
        )


class Application:
    """
    Orchestre le routage, les middlewares et le contrôle d'accès.

    Usage minimal (identique à avant) :
        app = Application(router)

    Avec middlewares personnalisés :
        app = Application(router, middlewares=[AuthMiddleware("/login"), MonMiddleware()])

    Chaque middleware doit exposer check(request) → Response | None.
    Les middlewares sont évalués dans l'ordre ; le premier qui retourne une
    Response court-circuite la chaîne.  Ils ne s'appliquent qu'aux routes
    protégées (is_public == False).

    Le CSRF est vérifié automatiquement pour les routes unsafe dont csrf=True,
    y compris lorsqu'elles sont publiques.

    Les routes API sont chargées optionnellement depuis mvc/api_routes.py si
    le fichier existe. Passer api_routes_module=None pour désactiver ce chargement.
    """

    def __init__(self, router: Router, middlewares: list[Any] | None = None, login_url: str = "/login",
                 csrf_middleware: Any = None, *, api_routes_module: str | None = "mvc.api_routes") -> None:
        self._router      = router
        self._middlewares = middlewares if middlewares is not None else [AuthMiddleware(login_url)]
        self._csrf        = csrf_middleware if csrf_middleware is not None else CsrfMiddleware()
        if api_routes_module:
            _load_api_routes(router, api_routes_module)

    def dispatch(self, request: Request) -> Response:
        try:
            result = self._router.match(request.method, request.path)
            if result is None:
                # CORE-HTTP-405-ALLOW-001 : distinguer un chemin inconnu (404)
                # d'un chemin connu appelé avec une mauvaise méthode (405 +
                # en-tête Allow, sémantique HTTP correcte).
                allowed = self._router.allowed_methods(request.path)
                if allowed:
                    response = _html("errors/405.html", 405)
                    response.headers["Allow"] = ", ".join(allowed)
                    return response
                return _html("errors/404.html", 404)

            route, params = result
            request.route_params = params

            if route.requires_csrf(request.method):
                denied = self._csrf.check(request)
                if denied:
                    return denied

            if not route.public:
                for middleware in self._middlewares:
                    denied = middleware.check(request)
                    if denied:
                        return denied

            return route.handler(request)

        except DatabaseUnavailableError:
            # Surcharge passagère, pas un défaut de l'application : toutes les
            # connexions étaient prises et aucune ne s'est libérée à temps
            # (MARIADB-POOL-QUEUE-001). Un 500 annoncerait un bug du serveur et
            # enverrait chercher une erreur dans le code, là où le remède est
            # d'élargir `DB_POOL_SIZE` ou de raccourcir les requêtes.
            logger.warning(
                "Base indisponible (capacité) — %s %s", request.method, request.path
            )
            response = _service_unavailable()
            response.headers["Retry-After"] = "2"
            return response

        except Exception as _exc:
            logger.exception("Erreur non gérée — %s %s", request.method, request.path)
            _log_runtime_error(_exc, request)
            # En APP_ENV=dev, la page 500 affiche la cause ; None en prod.
            return _html("errors/500.html", 500, _dev_error_context(_exc))
