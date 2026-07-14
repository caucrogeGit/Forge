"""Tests — CORE-WSGI-HEADERS-CONTRACT-001 : contrat commun des headers de requête.

`request.data` (convention d'inspection) itère `request.headers.keys()`.
Sur le serveur de dev, `headers` est un `http.client.HTTPMessage` ; sous WSGI,
c'est `_WsgiHeaders`, qui n'exposait que `get()` : `request.data` levait
`AttributeError` sur tout le chemin de production. Garde-fous :
  1. contrat commun `get`/`keys`/`items` honoré par les deux implémentations ;
  2. `request.data` fonctionne sous WSGI (reproduction du plantage corrigé) ;
  3. les headers sensibles restent masqués dans `request.data` sous WSGI.
"""
from __future__ import annotations

from email.parser import Parser

import pytest

from core.app.wsgi import _WsgiHandlerStub, _WsgiHeaders
from core.http.request import MASKED_VALUE, Request


def _environ(extra: dict | None = None) -> dict:
    env: dict = {
        "REQUEST_METHOD": "GET",
        "PATH_INFO": "/inspect",
        "QUERY_STRING": "",
        "REMOTE_ADDR": "127.0.0.1",
        "CONTENT_TYPE": "text/plain",
        "HTTP_X_CUSTOM": "valeur",
        "HTTP_AUTHORIZATION": "Bearer secret-token",
        "HTTP_COOKIE": "session_id=abc",
    }
    if extra:
        env.update(extra)
    return env


def _http_message():
    return Parser().parsestr(
        "X-Custom: valeur\r\nAuthorization: Bearer secret-token\r\n\r\n"
    )


@pytest.mark.parametrize("headers_factory", [
    lambda: _WsgiHeaders(_environ()),
    _http_message,
], ids=["wsgi", "httpmessage"])
class TestSharedContract:
    def test_get_present(self, headers_factory):
        headers = headers_factory()
        assert headers.get("X-Custom") == "valeur"

    def test_keys_iterable_et_contient_les_headers(self, headers_factory):
        headers = headers_factory()
        keys = [k.lower() for k in headers.keys()]
        assert "x-custom" in keys
        assert "authorization" in keys

    def test_items_coherent_avec_get(self, headers_factory):
        headers = headers_factory()
        for key, value in headers.items():
            assert headers.get(key) == value


class TestRequestDataUnderWsgi:
    def test_request_data_ne_leve_plus(self):
        request = Request(_WsgiHandlerStub(_environ()))
        data = request.data
        assert data["method"] == "GET"
        assert data["path"] == "/inspect"
        assert data["headers"].get("x-custom") == "valeur"

    def test_headers_sensibles_masques(self):
        request = Request(_WsgiHandlerStub(_environ()))
        headers = request.data["headers"]
        assert headers.get("authorization") == MASKED_VALUE
        assert headers.get("cookie") == MASKED_VALUE
