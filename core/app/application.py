# pyright: strict
from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from core.app.api_routes_loader import load_api_routes as _load_api_routes
from core.database.errors import DatabaseUnavailableError
from core.http.helpers import error_page as _error_page
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

    Ce repli, écrit ici en premier, est devenu la règle générale de toutes les
    pages d'erreur (`error_page`, `CORE-WSGI-CSRF-POST-001`). Cette fonction ne
    garde donc que ce qui lui est propre : un texte qui nomme la cause et
    invite à réessayer, ce que le repli générique ne peut pas deviner.
    """
    return _error_page(
        "errors/503.html",
        503,
        fallback=(
            "Service momentanement indisponible.\n"
            "Le service recoit plus de demandes qu'il ne peut en traiter ; "
            "reessayez dans quelques instants.\n"
        ),
    )


def _internal_error(exc: BaseException, request: Any, *, est_api: bool) -> Response:
    """Réponse 500, construite de façon à ne jamais pouvoir lever.

    Le rattrapage d'erreur est le seul code dont l'échec n'a pas de filet : il
    s'exécute déjà dans un bloc `except`, et ce qu'il lève ressort de
    `dispatch`. Le serveur répond alors à la place de Forge, sans les en-têtes
    de sécurité, et **la cause première est perdue** : l'exploitant lit
    l'erreur du gabarit d'erreur, pas celle qui a réellement échoué.

    Trois choses peuvent échouer ici, et les trois échouaient
    (`CORE-WSGI-ERROR-PATH-001`) :

    - le rendu de `errors/500.html`. Ce gabarit **appartient à l'utilisateur**,
      le squelette le livre et Forge n'y réécrit jamais (principe 4). Une
      syntaxe Jinja invalide, un filtre inconnu ou une variable absente y
      suffisaient, et `core.http.helpers.html` ne rattrape que le gabarit
      introuvable ;
    - l'écriture du journal, quand le disque est plein. C'est précisément le
      moment où la page d'erreur doit tenir ;
    - la construction du contexte de dev, qui inspecte l'exception et sa pile.

    Le repli suit `_service_unavailable` : minimal, en texte brut, sans
    dépendre de quoi que ce soit que le projet puisse avoir cassé.
    """
    from core.http.response import Response

    try:
        _log_runtime_error(exc, request)
    except Exception:  # noqa: BLE001 — journal indisponible, la réponse prime
        logger.exception("Le journal d'erreurs a échoué à son tour")

    if est_api:
        # Aucun détail sur l'erreur, même en dev. La page HTML peut afficher la
        # cause, elle est lue par un humain devant son navigateur ; une réponse
        # d'API part vers un client qui la journalise, la stocke ou la
        # réexpose. La cause reste dans les journaux du serveur.
        try:
            return _api_error(500, API_ERROR_INTERNAL)
        except Exception:  # noqa: BLE001
            logger.exception("La réponse d'erreur JSON a échoué à son tour")
            return Response(
                status=500,
                body=b'{"error":"internal_error"}',
                content_type="application/json; charset=utf-8",
            )

    try:
        # En APP_ENV=dev, la page 500 affiche la cause ; None en prod.
        contexte = _dev_error_context(exc)
    except Exception:  # noqa: BLE001 — l'introspection a échoué, pas la réponse
        logger.exception("Le contexte d'erreur de dev a échoué à son tour")
        contexte = None

    try:
        return _error_page("errors/500.html", 500, contexte)
    except Exception:  # noqa: BLE001 — le gabarit du projet est en défaut
        logger.exception("Le rendu de errors/500.html a échoué à son tour")

    return Response(
        status=500,
        body=(
            "Erreur interne du serveur.\n"
            "La cause a ete journalisee cote serveur.\n"
        ).encode("utf-8"),
        content_type="text/plain; charset=utf-8",
    )


#: Codes d'erreur des réponses d'API, stables et lisibles côté client.
#: La forme est celle de l'ADR-088, rendue par `core.http.json_error`, seule
#: fabrique de réponse d'erreur JSON du dépôt.
API_ERROR_UNAUTHENTICATED = "unauthenticated"
API_ERROR_FORBIDDEN = "forbidden"
API_ERROR_DENIED = "denied"
API_ERROR_UNAVAILABLE = "service_unavailable"
API_ERROR_INTERNAL = "internal_error"


def _api_error(status: int, code: str, source: "Response | None" = None) -> Response:
    """Réponse JSON d'erreur pour une route d'API.

    `source` est la réponse HTML ou la redirection que l'on remplace. Ses
    en-têtes sont repris, **cookies compris**, et c'est le point délicat :
    `AuthMiddleware` efface le cookie de session quand il détecte une session
    orpheline (ADR-080). Reconstruire la réponse sans les reprendre laisserait
    cette session ouverte, donc transformerait une correction de forme en
    régression de sécurité.

    `Location` est écarté, une réponse d'API ne redirigeant pas, et les en-têtes
    de corps le sont aussi puisque le corps change.
    """
    from core.http.helpers import json_error

    response = json_error(code, status)
    if source is not None:
        for cle, valeur in source.headers.items():
            if cle.lower() in ("location", "content-type", "content-length"):
                continue
            response.headers[cle] = valeur
        response.set_cookies.extend(source.set_cookies)
    return response


def _api_denial(denied: Response) -> Response:
    """Traduit en JSON le refus d'un middleware sur une route d'API.

    Une redirection devient un 401 : c'est le cœur de la promesse du drapeau
    `api`, un client JSON ne suit pas une redirection vers une page de
    connexion, il reçoit du HTML là où il attend des données et échoue loin de
    la cause.

    Un refus déjà explicite garde son statut, seule sa forme change. Un
    middleware applicatif qui rend 403 doit continuer de rendre 403.
    """
    if 300 <= denied.status < 400:
        return _api_error(401, API_ERROR_UNAUTHENTICATED, denied)
    code = API_ERROR_FORBIDDEN if denied.status == 403 else API_ERROR_DENIED
    return _api_error(denied.status, code, denied)


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
        # CORE-ROUTE-API-FLAG-001 : le drapeau `api` d'une route était déclaré,
        # propagé, affiché par `routes:list`, et **lu par aucun code**. La
        # documentation en promettait pourtant un comportement, « réponses
        # JSON, pas de redirection login ». Il le tient désormais, pour tout ce
        # que le framework rend APRÈS avoir trouvé la route.
        #
        # Le drapeau ne peut rien gouverner avant : sur un 404 aucune route
        # n'est trouvée, donc rien ne dit que le chemin visait une API. Les 404
        # et 405 restent en HTML, limite écrite dans la doc du routeur.
        est_api = False
        try:
            result = self._router.match(request.method, request.path)
            if result is None:
                # CORE-HTTP-405-ALLOW-001 : distinguer un chemin inconnu (404)
                # d'un chemin connu appelé avec une mauvaise méthode (405 +
                # en-tête Allow, sémantique HTTP correcte).
                allowed = self._router.allowed_methods(request.path)
                if allowed:
                    response = _error_page("errors/405.html", 405)
                    response.headers["Allow"] = ", ".join(allowed)
                    return response
                return _error_page("errors/404.html", 404)

            route, params = result
            request.route_params = params
            est_api = route.api

            if route.requires_csrf(request.method):
                denied = self._csrf.check(request)
                if denied:
                    return _api_error(denied.status, API_ERROR_FORBIDDEN, denied) if est_api else denied

            if not route.public:
                for middleware in self._middlewares:
                    denied = middleware.check(request)
                    if denied:
                        return _api_denial(denied) if est_api else denied

            reponse = route.handler(request)
            if route.no_store:
                # NO-STORE-ROUTE-FLAG-001 : posé ici, donc par les DEUX
                # serveurs, qui partagent `dispatch`. La règle vivait dans une
                # liste de chemins codée en dur du serveur de développement :
                # l'adaptateur WSGI ne la connaissait pas, et le déploiement de
                # production servait `/login` sans, un navigateur pouvant alors
                # conserver la page.
                #
                # `setdefault` : un contrôleur qui pose sa propre directive de
                # cache garde la main.
                _entetes: dict[str, str] | None = getattr(reponse, "headers", None)
                if isinstance(_entetes, dict):
                    _entetes.setdefault("Cache-Control", "no-store")
            return reponse

        except DatabaseUnavailableError as _indispo:
            # Condition passagère, pas un défaut de l'application : soit toutes
            # les connexions étaient prises et aucune ne s'est libérée à temps
            # (MARIADB-POOL-QUEUE-001), soit celle empruntée avait été fermée
            # par le serveur (DB-CONNECTION-LOST-503-001). Un 500 annoncerait un
            # bug du serveur et enverrait chercher une erreur dans le code.
            #
            # Le message de l'erreur distingue les deux, et l'exploitant en a
            # besoin : élargir `DB_POOL_SIZE` ne répare pas un serveur qui
            # redémarre, et attendre ne répare pas un pool trop étroit.
            logger.warning(
                "Base indisponible — %s %s : %s",
                request.method, request.path, _indispo,
            )
            response = (
                _api_error(503, API_ERROR_UNAVAILABLE) if est_api
                else _service_unavailable()
            )
            response.headers["Retry-After"] = "2"
            return response

        except Exception as _exc:
            logger.exception("Erreur non gérée — %s %s", request.method, request.path)
            # Journalisation, contexte et rendu vivent dans `_internal_error`,
            # qui ne peut pas lever : ce qui sortirait d'ici ressortirait de
            # `dispatch`, et le serveur répondrait à la place de Forge.
            return _internal_error(_exc, request, est_api=est_api)
