# pyright: strict
"""core/app/wsgi.py — Callables WSGI pour Forge.

Tickets :
- WSGI-ENTRYPOINT-001 : `create_wsgi_app(application)` — adaptateur minimal
  qui prend une `Application` déjà construite et retourne un callable WSGI ;
- WSGI-APP-FACTORY-CONFIG-001 : `create_configured_wsgi_app()` — charge la
  même configuration que `python app.py` (via `core.app.app_factory`) et
  retourne le callable WSGI prêt à l'emploi ;
- WSGI-PROD-WARNINGS-001 : `create_configured_wsgi_app()` émet aussi
  les warnings production (`MemorySessionStore` en `APP_ENV=prod`) — une
  seule fois à la construction de l'application, jamais par requête ;
- CORE-WSGI-HEALTH-PARITY-001 : `GET /health` répond `200 {"status": "ok"}`
  ici comme sur le serveur de développement. La sonde figure au contrat de
  stabilité, mais n'était servie que par ce dernier et répondait 404 derrière
  Gunicorn ; la réponse vient désormais de `core.http.health`, source unique ;
- CORE-WSGI-BODY-LIMIT-001 : le corps de requête est contrôlé contre
  `request_size_limit(...)` AVANT d'être lu (aucune allocation pour un
  `Content-Length` au-delà de la limite), il n'est lu que pour les méthodes
  à corps, et son dépassement répond 413 (plus jamais 400).

Usage typique — dans le `wsgi.py` de l'application :

    from core.app.wsgi import create_configured_wsgi_app

    application = create_configured_wsgi_app()

Puis exposer `application` à un serveur WSGI externe (ex.
`gunicorn wsgi:application`).

Périmètre :
- ne remplace pas `python app.py` (serveur de développement) ;
- ne sert pas les fichiers statiques (responsabilité du reverse proxy) ;
- ajoute le socle de headers de sécurité partagé avec `app.py` via
  `core.security.headers.apply_security_headers` (`WSGI-SECURITY-HEADERS-001`)
  — HSTS conditionné à `wsgi.url_scheme == "https"` ; derrière un reverse
  proxy TLS-terminé, c'est le proxy qui pose HSTS ;
- ne couvre pas la production complète — cf `DOCS-PRODUCTION-LIMITS-001`.
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from io import BytesIO
from typing import Any, Iterable

from core.http.health import health_response, is_health_request
from core.http.request import (
    BODY_METHODS,
    Request,
    RequestEntityTooLarge,
    request_size_limit,
)
from core.http.response import Response
from core.security import csp as _csp
from core.security.headers import apply_security_headers, assert_headers_are_safe


_REASONS = {
    200: "OK",
    201: "Created",
    204: "No Content",
    301: "Moved Permanently",
    302: "Found",
    303: "See Other",
    304: "Not Modified",
    400: "Bad Request",
    401: "Unauthorized",
    403: "Forbidden",
    404: "Not Found",
    405: "Method Not Allowed",
    413: "Payload Too Large",
    500: "Internal Server Error",
}


class _WsgiHeaders:
    """Vue insensible à la casse des headers HTTP extraits de `environ`.

    Contrat minimal partagé avec `http.client.HTTPMessage` (le type de
    `request.headers` sur le serveur de dev) : `get`, `keys`, `items`.
    `keys()`/`items()` sont requis par la convention d'inspection
    (`request.data`, `Response.debug`) — leur absence faisait lever
    `AttributeError` sur tout le chemin WSGI (CORE-WSGI-HEADERS-CONTRACT-001).
    """

    def __init__(self, environ: dict[str, Any]) -> None:
        normalized: dict[str, str] = {}
        if "CONTENT_TYPE" in environ:
            normalized["content-type"] = environ["CONTENT_TYPE"]
        if "CONTENT_LENGTH" in environ:
            normalized["content-length"] = str(environ["CONTENT_LENGTH"])
        for key, value in environ.items():
            if key.startswith("HTTP_"):
                normalized[key[5:].replace("_", "-").lower()] = value
        self._headers = normalized

    def get(self, name: str, default: str = "") -> str:
        return self._headers.get(name.lower(), default)

    def keys(self) -> list[str]:
        return list(self._headers.keys())

    def items(self) -> list[tuple[str, str]]:
        return list(self._headers.items())


class _WsgiHandlerStub:
    """Stub `handler` minimal pour instancier `core.http.Request`.

    Reproduit les seuls attributs lus par `Request.__init__` :
    `path`, `command`, `headers`, `client_address`, `rfile`.
    """

    def __init__(self, environ: dict[str, Any]) -> None:
        path = environ.get("PATH_INFO", "/") or "/"
        qs = environ.get("QUERY_STRING", "") or ""
        self.path = f"{path}?{qs}" if qs else path
        self.command = environ.get("REQUEST_METHOD", "GET")
        self.headers = _WsgiHeaders(environ)
        remote = environ.get("REMOTE_ADDR", "0.0.0.0") or "0.0.0.0"
        self.client_address = (remote, 0)
        try:
            length = int(environ.get("CONTENT_LENGTH") or 0)
        except (TypeError, ValueError):
            length = 0
        stream = environ.get("wsgi.input")
        # CORE-WSGI-BODY-LIMIT-001 : le corps n'est lu que pour les méthodes à
        # corps (aligné sur `Request`, qui ignore le corps des autres), et le
        # Content-Length annoncé est contrôlé AVANT toute lecture — un corps
        # trop grand est refusé sans jamais être chargé en mémoire.
        raw = b""
        if length > 0 and stream is not None and self.command in BODY_METHODS:
            content_type = self.headers.get("content-type", "")
            if length > request_size_limit(content_type):
                raise RequestEntityTooLarge(length)
            raw = stream.read(length)
        self.rfile = BytesIO(raw)


def _format_status(code: int) -> str:
    reason = _REASONS.get(code, "")
    return f"{code} {reason}".rstrip()


def _response_to_wsgi(
    response: Response,
    start_response: Callable[..., Any],
    *,
    is_https: bool = False,
) -> Iterable[bytes]:
    """Adapte une `Response` Forge en réponse WSGI avec headers de sécurité.

    Les headers de sécurité par défaut (X-Frame-Options, CSP, etc.) sont
    posés en `setdefault` via `core.security.headers.apply_security_headers`
    — une route applicative qui définit explicitement un de ces headers garde
    la main. HSTS est conditionné à `is_https=True` (cf
    `WSGI-SECURITY-HEADERS-001`).
    """
    # Corps : soit un itérable de streaming (Response.file → Range/206,
    # CORE-HTTP-FILE-RANGE-001), soit le `body` bytes habituel. Dans le cas
    # streaming, `Content-Length` vient de `response.content_length` (taille de
    # la tranche servie), pas de `len(body)`.
    stream = getattr(response, "stream", None)
    if stream is not None:
        body_iter: Iterable[bytes] = stream
        content_length = getattr(response, "content_length", None) or 0
    else:
        body = response.body
        body_iter = [body]
        content_length = len(body)

    # On part des headers applicatifs, on superpose les défauts de sécurité,
    # puis on construit la liste WSGI finale. Content-Type / Content-Length
    # restent en tête, calculés ici (jamais issus du dict applicatif).
    headers_dict: dict[str, str] = {str(k): str(v) for k, v in response.headers.items()}
    apply_security_headers(
        headers_dict,
        include_hsts=is_https,
        # Le nonce de la requête en cours, posé par le callable WSGI. `None`
        # quand `APP_CSP_NONCE_ENABLED` est absent, et la CSP reste alors
        # `script-src 'self'`, sans `unsafe-inline`.
        #
        # L'application peut toujours définir sa propre
        # `Content-Security-Policy` dans `response.headers` : le `setdefault`
        # la respecte.
        csp=_csp.build_csp_header(_csp.get_request_nonce()),
    )

    # CORE-HEADER-CRLF-001 : contrôle AVANT `start_response`, tant qu'aucune
    # ligne n'est partie. Un saut de ligne dans une valeur découperait la
    # réponse pour le client.
    assert_headers_are_safe(headers_dict)

    headers: list[tuple[str, str]] = [
        ("Content-Type", response.content_type),
        ("Content-Length", str(content_length)),
    ]
    # Content-Type / Content-Length sont calculés ici : on écarte toute clé
    # homonyme du dict applicatif (comparaison insensible à la casse) pour ne
    # pas émettre deux fois le même en-tête.
    _reserved = {"content-type", "content-length"}
    for key, value in headers_dict.items():
        if key.lower() in _reserved:
            continue
        headers.append((key, value))
    # Cookies additionnels : une ligne Set-Cookie par cookie accumulé via
    # response.add_cookie (CORE-RESPONSE-MULTI-COOKIE-001).
    for cookie in getattr(response, "set_cookies", []):
        headers.append(("Set-Cookie", str(cookie)))
    start_response(_format_status(response.status), headers)
    return body_iter


def create_wsgi_app(application: Any) -> Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]:
    """Retourne un callable WSGI qui dispatche via l'`Application` Forge fournie.

    `application` doit exposer `dispatch(request) -> Response`.
    """

    def app(environ: dict[str, Any], start_response: Callable[..., Any]) -> Iterable[bytes]:
        # CORE-WSGI-CSP-NONCE-001 : le nonce est posé pour toute la durée de la
        # requête, exactement comme le fait le serveur de développement. Sans
        # lui, `APP_CSP_NONCE_ENABLED` n'agissait qu'en développement alors que
        # la documentation le prescrit en production, et le script inline d'un
        # gabarit était silencieusement bloqué une fois déployé.
        #
        # L'enveloppe couvre le rendu ET la construction de l'en-tête : le
        # gabarit et la CSP doivent voir la même valeur, faute de quoi le
        # mécanisme ne sert à rien.
        with _csp.request_nonce(
            _csp.generate_nonce() if _csp.nonce_enabled() else None
        ):
            return _repondre(environ, start_response)

    def _repondre(
        environ: dict[str, Any], start_response: Callable[..., Any]
    ) -> Iterable[bytes]:
        is_https = environ.get("wsgi.url_scheme") == "https"
        try:
            handler = _WsgiHandlerStub(environ)
            request = Request(handler)
        except RequestEntityTooLarge:
            # CORE-WSGI-BODY-LIMIT-001 : un corps au-delà de la limite est un
            # 413 explicite (comme le serveur de dev), pas un 400 générique.
            too_large = Response(
                status=413,
                body=b"Payload Too Large",
                content_type="text/plain; charset=utf-8",
            )
            return _response_to_wsgi(too_large, start_response, is_https=is_https)
        except Exception:
            # Même le 400 d'entrée ne doit pas être moins protégé que la
            # réponse nominale : on passe par _response_to_wsgi pour profiter
            # du socle de headers de sécurité.
            bad_request = Response(
                status=400,
                body=b"Bad Request",
                content_type="text/plain; charset=utf-8",
            )
            return _response_to_wsgi(bad_request, start_response, is_https=is_https)
        # CORE-WSGI-HEALTH-PARITY-001 : la sonde du contrat de stabilité, servie
        # avant le routage comme sur le serveur de dev. Elle n'était traitée que
        # par ce dernier, et répondait 404 derrière Gunicorn.
        if is_health_request(request.path):
            return _response_to_wsgi(
                health_response(), start_response, is_https=is_https)
        response = application.dispatch(request)
        return _response_to_wsgi(response, start_response, is_https=is_https)

    return app


def create_configured_wsgi_app(
    *,
    emit_prod_warnings: bool = True,
    logger: logging.Logger | None = None,
) -> Callable[[dict[str, Any], Callable[..., Any]], Iterable[bytes]]:
    """Construit l'`Application` Forge configurée et retourne le callable WSGI.

    Source unique d'initialisation : charge la même configuration que
    `python app.py` via `core.app.app_factory.build_application`, puis enveloppe
    l'application dans un adaptateur WSGI standard.

    Garantit que les paramètres `forge.configure(...)` (dont
    `trusted_proxies`) sont appliqués avant que la première requête WSGI
    ne soit dispatched.

    Si `emit_prod_warnings=True` (défaut), émet une seule fois — à la
    construction, pas à chaque requête — les avertissements production
    de `core.app.prod_warnings` (ex. `MemorySessionStore` en `APP_ENV=prod`).
    Passer `emit_prod_warnings=False` pour les tests qui ne veulent pas
    polluer le logger.
    """
    import core.forge as forge
    from core.app.app_factory import build_application
    from core.app.prod_warnings import emit_memory_store_warning_if_needed

    application = build_application()
    if emit_prod_warnings:
        emit_memory_store_warning_if_needed(
            str(forge.get("app_env") or ""),
            forge.get("session_store"),
            logger=logger,
        )
    return create_wsgi_app(application)
