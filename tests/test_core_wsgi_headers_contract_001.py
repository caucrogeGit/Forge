"""Tests — CORE-WSGI-HEADERS-CONTRACT-001 : contrat commun des headers de requête.

`request.data` (convention d'inspection) itère `request.headers.keys()`.
Sur le serveur de dev, `headers` est un `http.client.HTTPMessage` ; sous WSGI,
c'était une classe maison qui n'exposait que `get()` : `request.data` levait
`AttributeError` sur tout le chemin de production. Garde-fous :
  1. contrat commun `get`/`keys`/`items` honoré par les deux implémentations ;
  2. `request.data` fonctionne sous WSGI (reproduction du plantage corrigé) ;
  3. les headers sensibles restent masqués dans `request.data` sous WSGI.

Ce fichier a une limite, révélée par `CORE-WSGI-HEADERS-PARITY-001` : il joue
les deux implémentations sur des jeux d'en-têtes DIFFÉRENTS, donc il vérifie
que chacune tient un contrat, jamais que les deux répondent la même chose. Dix
écarts ont vécu sous lui. La comparaison côte à côte vit désormais dans
`tests/test_core_wsgi_headers_parity_001.py`.
"""
from __future__ import annotations

from email.parser import Parser

import pytest

from core.app.wsgi import _headers_from_environ, _WsgiHandlerStub
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
    lambda: _headers_from_environ(_environ()),
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
        # Les clés portent la casse HTTP usuelle, comme sur le serveur de
        # développement. Elles sortaient en minuscules sous WSGI, faute d'un
        # type commun (CORE-WSGI-HEADERS-PARITY-001).
        assert data["headers"].get("X-Custom") == "valeur"

    def test_headers_sensibles_masques(self):
        request = Request(_WsgiHandlerStub(_environ()))
        headers = request.data["headers"]
        assert headers.get("Authorization") == MASKED_VALUE
        assert headers.get("Cookie") == MASKED_VALUE
