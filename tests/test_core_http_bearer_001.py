"""Tests — CORE-HTTP-BEARER-PRIMITIVE-001 : primitive Bearer partagée du cœur.

Le bloc d'autorisation Bearer optionnelle (mode ouvert sans jeton, sinon
`Authorization: Bearer <token>` comparé en temps constant) était dupliqué à
l'identique dans forge-mvc-video, forge-mvc-audio et forge-mvc-iot. Il vit
désormais dans `core/http/bearer.py`, testé une fois pour toutes.

Garde-fous du contrat :
  1. `extract_bearer_token` : en-tête absent, schéma erroné, extraction correcte ;
  2. `is_bearer_authorized` : mode ouvert (jeton None), jeton correct, jeton
     erroné, en-tête absent ;
  3. le jeton est comparé avec `secrets.compare_digest` (temps constant).
"""
from __future__ import annotations

import inspect
from typing import Any

from core.http.bearer import (
    BEARER_PREFIX,
    extract_bearer_token,
    is_bearer_authorized,
)


class FakeRequest:
    """Objet de requête minimal : seul `header(name, default)` est requis."""

    def __init__(self, headers: dict[str, str] | None = None) -> None:
        self._headers = headers or {}

    def header(self, name: str, default: Any = None) -> Any:
        return self._headers.get(name, default)


def _with_auth(value: str) -> FakeRequest:
    return FakeRequest({"Authorization": value})


class TestExtractBearerToken:
    def test_extrait_le_jeton(self):
        assert extract_bearer_token(_with_auth("Bearer abc123")) == "abc123"

    def test_header_absent(self):
        assert extract_bearer_token(FakeRequest()) is None

    def test_schema_errone(self):
        assert extract_bearer_token(_with_auth("Basic abc123")) is None

    def test_prefixe_seul_donne_jeton_vide(self):
        # « Bearer » sans espace n'est pas le préfixe ; « Bearer » + espace + rien = "".
        assert extract_bearer_token(_with_auth("Bearer")) is None
        assert extract_bearer_token(_with_auth(BEARER_PREFIX)) == ""


class TestIsBearerAuthorized:
    def test_mode_ouvert_sans_jeton_configure(self):
        assert is_bearer_authorized(FakeRequest(), None) is True

    def test_jeton_correct(self):
        assert is_bearer_authorized(_with_auth("Bearer s3cr3t"), "s3cr3t") is True

    def test_jeton_errone(self):
        assert is_bearer_authorized(_with_auth("Bearer wrong"), "s3cr3t") is False

    def test_header_absent_avec_jeton_configure(self):
        assert is_bearer_authorized(FakeRequest(), "s3cr3t") is False

    def test_schema_errone_avec_jeton_configure(self):
        assert is_bearer_authorized(_with_auth("Basic s3cr3t"), "s3cr3t") is False


def test_comparaison_temps_constant():
    # La comparaison de jeton doit passer par secrets.compare_digest (anti-timing).
    source = inspect.getsource(is_bearer_authorized)
    assert "compare_digest" in source, (
        "is_bearer_authorized doit comparer le jeton en temps constant "
        "(secrets.compare_digest)."
    )
