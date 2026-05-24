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
- n'ajoute pas d'en-têtes de sécurité (ils restent dans `app.py`
  ou dans la configuration du reverse proxy) ;
- ne couvre pas la production complète — cf `DOCS-PRODUCTION-LIMITS-001`.
"""
from __future__ import annotations

import logging
from io import BytesIO
from typing import Iterable

from core.http.request import Request
from core.http.response import Response


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


def _response_to_wsgi(response: Response, start_response) -> Iterable[bytes]:
    body = response.body if response.body is not None else b""
    headers: list[tuple[str, str]] = [
        ("Content-Type", response.content_type),
        ("Content-Length", str(len(body))),
    ]
    for key, value in response.headers.items():
        headers.append((str(key), str(value)))
    start_response(_format_status(response.status), headers)
    return [body]


def create_wsgi_app(application):
    """Retourne un callable WSGI qui dispatche via l'`Application` Forge fournie.

    `application` doit exposer `dispatch(request) -> Response`.
    """

    def app(environ, start_response):
        handler = _WsgiHandlerStub(environ)
        try:
            request = Request(handler)
        except Exception:
            start_response(
                _format_status(400),
                [("Content-Type", "text/plain; charset=utf-8")],
            )
            return [b"Bad Request"]
        response = application.dispatch(request)
        return _response_to_wsgi(response, start_response)

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
