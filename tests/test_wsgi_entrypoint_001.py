"""Tests — WSGI-ENTRYPOINT-001 : callable WSGI minimal pour Forge.

Vérifie que `core.wsgi.create_wsgi_app(application)` :
  1. retourne un callable acceptant `(environ, start_response)` ;
  2. dispatche correctement une requête GET ;
  3. dispatche une requête POST avec body url-encoded ;
  4. relaie le statut, le content-type et les headers personnalisés
     vers `start_response` au format WSGI ;
  5. retourne un itérable de bytes (jamais un str) ;
  6. gère les routes inconnues via la 404 Forge.

Aucun socket n'est ouvert : tout passe par dispatch() en mémoire.
"""
from __future__ import annotations

from io import BytesIO

import pytest

from core.application import Application
from core.http.response import Response
from core.http.router import Router
from core.templating.manager import template_manager
from core.wsgi import create_wsgi_app


class _StubRenderer:
    """Renderer minimal — évite la dépendance Jinja dans ces tests."""

    def render(self, template: str, context: dict) -> str:
        return f"[{template}]"


@pytest.fixture(autouse=True)
def _stub_renderer():
    previous = template_manager._renderer
    template_manager.register(_StubRenderer())
    try:
        yield
    finally:
        template_manager._renderer = previous


# ── Helpers ──────────────────────────────────────────────────────────────────


def _capture():
    """Renvoie (start_response, captured) — captured a `status` et `headers`."""
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers
        return lambda chunk: None  # write callable — non utilisé ici

    return start_response, captured


def _environ(method="GET", path="/", query="", body=b"",
             content_type=None, extra=None):
    env: dict = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": query,
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": BytesIO(body),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }
    if body:
        env["CONTENT_LENGTH"] = str(len(body))
    if content_type:
        env["CONTENT_TYPE"] = content_type
    if extra:
        env.update(extra)
    return env


def _build_app():
    router = Router()

    def home(request):
        return Response(200, "Hello WSGI")

    def echo(request):
        name = request.body.get("name", [""])[0]
        return Response(
            200,
            f"echo:{name}",
            content_type="text/plain; charset=utf-8",
            headers={"X-Custom": "yes"},
        )

    router.add("GET", "/", home, public=True, csrf=False)
    router.add("POST", "/echo", echo, public=True, csrf=False)
    return Application(router, middlewares=[], api_routes_module=None)


@pytest.fixture
def wsgi_app():
    return create_wsgi_app(_build_app())


# ── Forme et contrats WSGI ──────────────────────────────────────────────────


class TestCallableShape:
    def test_module_imports(self):
        import core.wsgi as wsgi_mod
        assert hasattr(wsgi_mod, "create_wsgi_app")

    def test_factory_returns_callable(self, wsgi_app):
        assert callable(wsgi_app)

    def test_accepts_environ_and_start_response(self, wsgi_app):
        start_response, _ = _capture()
        result = wsgi_app(_environ(), start_response)
        # Consomme l'itérable pour éviter les ressources non libérées.
        list(result)

    def test_returns_iterable_of_bytes(self, wsgi_app):
        start_response, _ = _capture()
        chunks = list(wsgi_app(_environ(), start_response))
        assert chunks, "WSGI app must yield at least one chunk"
        for chunk in chunks:
            assert isinstance(chunk, bytes), (
                f"WSGI body chunk doit être bytes, reçu {type(chunk).__name__}"
            )


# ── Dispatch ────────────────────────────────────────────────────────────────


class TestGetRequest:
    def test_status_format_is_wsgi(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ("GET", "/"), start_response))
        assert captured["status"] == "200 OK"

    def test_body_matches_handler(self, wsgi_app):
        start_response, _ = _capture()
        body = b"".join(wsgi_app(_environ("GET", "/"), start_response))
        assert body == b"Hello WSGI"

    def test_headers_are_list_of_str_tuples(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ("GET", "/"), start_response))
        headers = captured["headers"]
        assert isinstance(headers, list)
        for entry in headers:
            assert isinstance(entry, tuple) and len(entry) == 2
            assert isinstance(entry[0], str) and isinstance(entry[1], str)

    def test_content_type_and_length_present(self, wsgi_app):
        start_response, captured = _capture()
        body = b"".join(wsgi_app(_environ("GET", "/"), start_response))
        keys = {k for k, _ in captured["headers"]}
        assert "Content-Type" in keys
        assert "Content-Length" in keys
        cl = dict(captured["headers"])["Content-Length"]
        assert cl == str(len(body))


class TestPostRequest:
    def test_url_encoded_body_reaches_handler(self, wsgi_app):
        start_response, captured = _capture()
        env = _environ(
            "POST",
            "/echo",
            body=b"name=Roger",
            content_type="application/x-www-form-urlencoded",
        )
        body = b"".join(wsgi_app(env, start_response))
        assert captured["status"] == "200 OK"
        assert body == b"echo:Roger"

    def test_custom_response_headers_relayed(self, wsgi_app):
        start_response, captured = _capture()
        env = _environ(
            "POST",
            "/echo",
            body=b"name=x",
            content_type="application/x-www-form-urlencoded",
        )
        list(wsgi_app(env, start_response))
        assert ("X-Custom", "yes") in captured["headers"]


class TestUnknownRoute:
    def test_returns_404(self, wsgi_app):
        start_response, captured = _capture()
        list(wsgi_app(_environ("GET", "/does-not-exist"), start_response))
        assert captured["status"].startswith("404"), captured["status"]


# ── Préservation de app.py ──────────────────────────────────────────────────


class TestAppPyUnaffected:
    """python app.py n'a pas été modifié ni cassé par ce ticket."""

    def test_app_module_is_importable(self):
        # app.py démarre le serveur dans __main__, l'import doit rester safe.
        import importlib
        mod = importlib.import_module("app")
        assert mod is not None
