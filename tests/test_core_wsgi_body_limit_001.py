"""Tests — CORE-WSGI-BODY-LIMIT-001 : corps WSGI borné avant lecture + 413.

Garde-fous :
  1. un POST dont le Content-Length dépasse la limite répond 413 sans que
     `wsgi.input` ne soit jamais lu (aucune allocation du corps) ;
  2. le 413 passe par le socle de headers de sécurité ;
  3. un POST sous la limite continue de fonctionner (non-régression) ;
  4. une méthode sans corps (GET) n'entraîne aucune lecture de `wsgi.input`,
     même avec un Content-Length énorme — aligné sur `Request`, qui ignore
     le corps des méthodes hors BODY_METHODS ;
  5. la limite multipart suit `upload_max_size` (contrat `request_size_limit`).

Aucun socket n'est ouvert : tout passe par le callable WSGI en mémoire.
"""
from __future__ import annotations

from io import BytesIO

import pytest

from core.app.application import Application
from core.app.wsgi import create_wsgi_app
from core.http.request import MAX_BODY_SIZE, request_size_limit
from core.http.response import Response
from core.http.router import Router


class _ExplosiveStream:
    """Flux qui échoue si on tente de le lire — prouve l'absence d'allocation."""

    def __init__(self) -> None:
        self.read_called = False

    def read(self, *args, **kwargs):
        self.read_called = True
        raise AssertionError("wsgi.input ne doit pas être lu pour un corps refusé")


def _capture():
    captured = {"status": None, "headers": None}

    def start_response(status, headers, exc_info=None):
        captured["status"] = status
        captured["headers"] = headers
        return lambda chunk: None

    return start_response, captured


def _environ(method="POST", path="/echo", body=b"", content_length=None,
             content_type="application/x-www-form-urlencoded", stream=None):
    env: dict = {
        "REQUEST_METHOD": method,
        "PATH_INFO": path,
        "QUERY_STRING": "",
        "SERVER_NAME": "test",
        "SERVER_PORT": "80",
        "SERVER_PROTOCOL": "HTTP/1.1",
        "REMOTE_ADDR": "127.0.0.1",
        "wsgi.input": stream if stream is not None else BytesIO(body),
        "wsgi.errors": BytesIO(),
        "wsgi.url_scheme": "http",
    }
    length = content_length if content_length is not None else len(body)
    if length:
        env["CONTENT_LENGTH"] = str(length)
    if content_type:
        env["CONTENT_TYPE"] = content_type
    return env


def _build_app():
    router = Router()

    def home(request):
        return Response(200, "ok")

    def echo(request):
        name = request.body.get("name", [""])[0]
        return Response(200, f"echo:{name}", content_type="text/plain; charset=utf-8")

    router.add("GET", "/", home, public=True, csrf=False)
    router.add("POST", "/echo", echo, public=True, csrf=False)
    return Application(router, middlewares=[], api_routes_module=None)


@pytest.fixture
def wsgi_app():
    return create_wsgi_app(_build_app())


class TestOversizedBodyRejectedBeforeRead:
    def test_repond_413(self, wsgi_app):
        start_response, captured = _capture()
        stream = _ExplosiveStream()
        env = _environ(content_length=MAX_BODY_SIZE + 1, stream=stream)
        body = b"".join(wsgi_app(env, start_response))
        assert captured["status"] == "413 Payload Too Large"
        assert body == b"Payload Too Large"

    def test_wsgi_input_jamais_lu(self, wsgi_app):
        start_response, _ = _capture()
        stream = _ExplosiveStream()
        env = _environ(content_length=10 * 1024 * 1024 * 1024, stream=stream)  # 10 Go annoncés
        list(wsgi_app(env, start_response))
        assert stream.read_called is False

    def test_413_porte_les_headers_de_securite(self, wsgi_app):
        start_response, captured = _capture()
        env = _environ(content_length=MAX_BODY_SIZE + 1, stream=_ExplosiveStream())
        list(wsgi_app(env, start_response))
        keys = {k for k, _ in captured["headers"]}
        assert "X-Frame-Options" in keys
        assert "Content-Security-Policy" in keys


class TestNominalUnchanged:
    def test_post_sous_la_limite_passe(self, wsgi_app):
        start_response, captured = _capture()
        env = _environ(body=b"name=Roger")
        body = b"".join(wsgi_app(env, start_response))
        assert captured["status"] == "200 OK"
        assert body == b"echo:Roger"

    def test_get_ignore_content_length_enorme_sans_lire(self, wsgi_app):
        start_response, captured = _capture()
        stream = _ExplosiveStream()
        env = _environ(method="GET", path="/", content_length=999_999_999,
                       content_type=None, stream=stream)
        body = b"".join(wsgi_app(env, start_response))
        assert captured["status"] == "200 OK"
        assert body == b"ok"
        assert stream.read_called is False


class TestMultipartLimitContract:
    def test_limite_multipart_suit_upload_max_size(self, monkeypatch):
        import core.forge as forge

        monkeypatch.setitem(forge._cfg, "upload_max_size", 5 * MAX_BODY_SIZE)
        limit = request_size_limit("multipart/form-data; boundary=x")
        assert limit == 5 * MAX_BODY_SIZE + 65_536
        assert request_size_limit("application/json") == MAX_BODY_SIZE
