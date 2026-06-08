import logging
from core.app.api_routes_loader import load_api_routes as _load_api_routes
from core.http.helpers import html as _html
from core.http.router import Router
from core.errors.runtime_error_logger import (
    build_dev_error_context as _dev_error_context,
    log_runtime_error as _log_runtime_error,
)
from core.security.middleware import AuthMiddleware, CsrfMiddleware

logger = logging.getLogger(__name__)


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

    def __init__(self, router: Router, middlewares=None, login_url: str = "/login",
                 csrf_middleware=None, *, api_routes_module: str | None = "mvc.api_routes"):
        self._router      = router
        self._middlewares = middlewares if middlewares is not None else [AuthMiddleware(login_url)]
        self._csrf        = csrf_middleware if csrf_middleware is not None else CsrfMiddleware()
        if api_routes_module:
            _load_api_routes(router, api_routes_module)

    def dispatch(self, request):
        try:
            result = self._router.match(request.method, request.path)
            if result is None:
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

        except Exception as _exc:
            logger.exception("Erreur non gérée — %s %s", request.method, request.path)
            _log_runtime_error(_exc, request)
            # En APP_ENV=dev, la page 500 affiche la cause ; None en prod.
            return _html("errors/500.html", 500, _dev_error_context(_exc))
