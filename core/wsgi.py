"""core/wsgi.py — Callables WSGI pour Forge.

Tickets :
- WSGI-ENTRYPOINT-001 : `create_wsgi_app(application)` — adaptateur minimal
  qui prend une `Application` déjà construite et retourne un callable WSGI ;
- WSGI-APP-FACTORY-CONFIG-001 : `create_configured_wsgi_app()` — charge la
  même configuration que `python app.py` (via `core.app_factory`) et
  retourne le callable WSGI prêt à l'emploi ;
- WSGI-PROD-WARNINGS-001 : `create_configured_wsgi_app()` émet aussi
  les warnings production (`MemorySessionStore` en `APP_ENV=prod`) — une
  seule fois à la construction de l'application, jamais par requête.

Usage typique — dans le `wsgi.py` de l'application :

    from core.wsgi import create_configured_wsgi_app

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
from io import BytesIO
from typing import Iterable

from core.http.request import Request
from core.http.response import Response
from core.security import csp as _csp
from core.security.headers import apply_security_headers


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

    Forge accède aux headers via `request.headers.get(name, default)` — cette
    interface suffit, pas besoin de mimer `http.client.HTTPMessage` au complet.
    """

    def __init__(self, environ: dict):
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


class _WsgiHandlerStub:
    """Stub `handler` minimal pour instancier `core.http.Request`.

    Reproduit les seuls attributs lus par `Request.__init__` :
    `path`, `command`, `headers`, `client_address`, `rfile`.
    """

    def __init__(self, environ: dict):
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
        raw = stream.read(length) if (length > 0 and stream is not None) else b""
        self.rfile = BytesIO(raw)


def _format_status(code: int) -> str:
    reason = _REASONS.get(code, "")
    return f"{code} {reason}".rstrip()


def _response_to_wsgi(
    response: Response,
    start_response,
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
        body = response.body if response.body is not None else b""
        body_iter = [body]
        content_length = len(body)

    # On part des headers applicatifs, on superpose les défauts de sécurité,
    # puis on construit la liste WSGI finale. Content-Type / Content-Length
    # restent en tête, calculés ici (jamais issus du dict applicatif).
    headers_dict: dict[str, str] = {str(k): str(v) for k, v in response.headers.items()}
    apply_security_headers(
        headers_dict,
        include_hsts=is_https,
        # En WSGI on n'a pas (encore) de nonce CSP par requête : on pose une
        # CSP par défaut sans nonce. L'application peut toujours définir sa
        # propre `Content-Security-Policy` dans `response.headers` — le
        # setdefault la respecte.
        csp=_csp.build_csp_header(None),
    )

    headers: list[tuple[str, str]] = [
        ("Content-Type", response.content_type),
        ("Content-Length", str(content_length)),
    ]
    for key, value in headers_dict.items():
        headers.append((key, value))
    start_response(_format_status(response.status), headers)
    return body_iter


def create_wsgi_app(application):
    """Retourne un callable WSGI qui dispatche via l'`Application` Forge fournie.

    `application` doit exposer `dispatch(request) -> Response`.
    """

    def app(environ, start_response):
        is_https = environ.get("wsgi.url_scheme") == "https"
        handler = _WsgiHandlerStub(environ)
        try:
            request = Request(handler)
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
        response = application.dispatch(request)
        return _response_to_wsgi(response, start_response, is_https=is_https)

    return app


def create_configured_wsgi_app(
    *,
    emit_prod_warnings: bool = True,
    logger: logging.Logger | None = None,
):
    """Construit l'`Application` Forge configurée et retourne le callable WSGI.

    Source unique d'initialisation : charge la même configuration que
    `python app.py` via `core.app_factory.build_application`, puis enveloppe
    l'application dans un adaptateur WSGI standard.

    Garantit que les paramètres `forge.configure(...)` (dont
    `trusted_proxies`) sont appliqués avant que la première requête WSGI
    ne soit dispatched.

    Si `emit_prod_warnings=True` (défaut), émet une seule fois — à la
    construction, pas à chaque requête — les avertissements production
    de `core.prod_warnings` (ex. `MemorySessionStore` en `APP_ENV=prod`).
    Passer `emit_prod_warnings=False` pour les tests qui ne veulent pas
    polluer le logger.
    """
    import core.forge as forge
    from core.app_factory import build_application
    from core.prod_warnings import emit_memory_store_warning_if_needed

    application = build_application()
    if emit_prod_warnings:
        emit_memory_store_warning_if_needed(
            str(forge.get("app_env") or ""),
            forge.get("session_store"),
            logger=logger,
        )
    return create_wsgi_app(application)
