"""Tests — SECURITY-API-AUTH-COMPARE-DIGEST-001.

Garde-fou : la comparaison du token Bearer API doit se faire en temps
constant via `hmac.compare_digest`, pas par `==`.

Origine : audit post-publication 1.0.0-beta.8. `core/security/api_auth.py`
utilisait deux comparaisons directes (`token == expected` dans
`is_valid_api_token` et `parts[1] != expected` dans `require_api_token`),
exposant le secret à un timing attack.

Ce module verrouille :
  1. les contrats fonctionnels existants restent identiques (valide
     accepté, invalide refusé, absent refusé) ;
  2. le module importe `hmac` et utilise `hmac.compare_digest` ;
  3. la comparaison directe sur `expected` a disparu.
"""
from __future__ import annotations

import inspect
from pathlib import Path

import pytest

from core.security import api_auth
from core.security.api_auth import is_valid_api_token, require_api_token
from forge_mvc_testing import FakeRequest


def _req(auth_header=None):
    headers = {}
    if auth_header is not None:
        headers["Authorization"] = auth_header
    return FakeRequest("GET", "/api/status", headers=headers)


class TestFunctionalContractPreserved:
    """is_valid_api_token et require_api_token conservent leur sémantique."""

    def test_valid_token_accepted(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "good-secret")
        assert is_valid_api_token(_req("Bearer good-secret")) is True

    def test_wrong_token_refused(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "good-secret")
        assert is_valid_api_token(_req("Bearer wrong")) is False

    def test_absent_token_refused(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "good-secret")
        assert is_valid_api_token(_req()) is False

    def test_empty_configured_token_refuses_all(self, monkeypatch):
        monkeypatch.setenv("API_TOKEN", "")
        assert is_valid_api_token(_req("Bearer anything")) is False

    @pytest.mark.parametrize("provided,expected,want", [
        ("a", "a", True),
        ("a", "b", False),
        ("", "a", False),
        ("a-very-long-token-value", "a-very-long-token-value", True),
        ("a-very-long-token-valuE", "a-very-long-token-value", False),
    ])
    def test_decorator_matches(self, monkeypatch, provided, expected, want):
        monkeypatch.setenv("API_TOKEN", expected)
        called = {"hit": False}

        @require_api_token
        def handler(request):
            called["hit"] = True
            from core.http import api_success
            return api_success({"ok": True})

        resp = handler(_req(f"Bearer {provided}"))
        assert called["hit"] is want
        assert resp.status == (200 if want else 401)


class TestConstantTimeCompareUsed:
    """Structurel : le module utilise bien hmac.compare_digest."""

    def test_hmac_imported(self):
        source = Path(inspect.getsourcefile(api_auth)).read_text(encoding="utf-8")
        assert "import hmac" in source, (
            "core/security/api_auth.py doit importer le module `hmac` "
            "pour utiliser compare_digest."
        )

    def test_compare_digest_used(self):
        source = Path(inspect.getsourcefile(api_auth)).read_text(encoding="utf-8")
        assert "hmac.compare_digest" in source, (
            "Le token Bearer doit être comparé via hmac.compare_digest "
            "pour éviter un timing attack."
        )

    def test_no_direct_equality_against_expected(self):
        source = Path(inspect.getsourcefile(api_auth)).read_text(encoding="utf-8")
        # Les motifs d'origine, dans les deux fonctions concernées.
        forbidden_patterns = (
            "token == expected",
            "parts[1] != expected",
            "parts[1] == expected",
        )
        offenders = [p for p in forbidden_patterns if p in source]
        assert not offenders, (
            f"Comparaison sensible directe encore présente : {offenders}. "
            "Utiliser hmac.compare_digest à la place."
        )
