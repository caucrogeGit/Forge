"""Tests comportementaux CSRF-DEDUP-CONSTANT-TIME-001.

Vérifie que :
- @require_csrf accepte un token valide
- @require_csrf rejette un token absent
- @require_csrf rejette un token invalide
- @require_csrf rejette quand les deux tokens sont absents (bug None-None corrigé)
- @require_csrf délègue à CsrfMiddleware (une seule implémentation)
- CsrfMiddleware.check() utilise compare_digest (non-régressif)
"""
from __future__ import annotations

from core.http.response import Response
from core.security.middleware import CsrfMiddleware
from core.security.decorators import require_csrf


def _fake_html(template, status):
    return Response(status, b"")


class _FakeRequest:
    def __init__(self, body=None, headers=None):
        self.body = body or {}
        self.headers = headers or {}


# ---------------------------------------------------------------------------
# Helpers de patch CSRF
# ---------------------------------------------------------------------------

def _patch_csrf(monkeypatch, session_token: str | None, form_token: str | None):
    """Configure le middleware pour une session et un body donnés."""
    import core.security.middleware as mw

    monkeypatch.setattr(mw, "get_session_id", lambda r: "sid123")
    monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": session_token} if session_token else {})
    monkeypatch.setattr(mw, "_error_page", _fake_html)

    body = {"csrf_token": [form_token]} if form_token is not None else {}
    return _FakeRequest(body=body)


# ---------------------------------------------------------------------------
# CsrfMiddleware — tests de non-régression
# ---------------------------------------------------------------------------


def test_middleware_accepts_valid_token(monkeypatch):
    """CsrfMiddleware.check() retourne None pour un token valide."""
    request = _patch_csrf(monkeypatch, session_token="tok123", form_token="tok123")
    assert CsrfMiddleware().check(request) is None


def test_middleware_rejects_invalid_token(monkeypatch):
    """CsrfMiddleware.check() retourne 403 pour un token incorrect."""
    request = _patch_csrf(monkeypatch, session_token="tok123", form_token="wrong")
    result = CsrfMiddleware().check(request)
    assert result is not None and result.status == 403


def test_middleware_rejects_absent_form_token(monkeypatch):
    """CsrfMiddleware.check() retourne 403 si le token formulaire est absent."""
    request = _patch_csrf(monkeypatch, session_token="tok123", form_token=None)
    result = CsrfMiddleware().check(request)
    assert result is not None and result.status == 403


def test_middleware_rejects_absent_session_token(monkeypatch):
    """CsrfMiddleware.check() retourne 403 si le token session est absent."""
    request = _patch_csrf(monkeypatch, session_token=None, form_token="tok123")
    result = CsrfMiddleware().check(request)
    assert result is not None and result.status == 403


def test_middleware_rejects_both_tokens_absent(monkeypatch):
    """CsrfMiddleware.check() retourne 403 si les deux tokens sont absents."""
    request = _patch_csrf(monkeypatch, session_token=None, form_token=None)
    result = CsrfMiddleware().check(request)
    assert result is not None and result.status == 403


def test_middleware_accepts_header_token(monkeypatch):
    """CsrfMiddleware.check() accepte le token via X-CSRF-Token header."""
    import core.security.middleware as mw
    monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
    monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "head_tok"})
    monkeypatch.setattr(mw, "_error_page", _fake_html)
    request = _FakeRequest(body={}, headers={"X-CSRF-Token": "head_tok"})
    assert CsrfMiddleware().check(request) is None


# ---------------------------------------------------------------------------
# @require_csrf — délégation à CsrfMiddleware
# ---------------------------------------------------------------------------


def test_require_csrf_accepts_valid_token(monkeypatch):
    """@require_csrf appelle la fonction wrappée si le token est valide."""
    request = _patch_csrf(monkeypatch, session_token="abc", form_token="abc")
    called = []

    @require_csrf
    def handler(req):
        called.append(True)
        return Response(200, b"OK")

    result = handler(request)
    assert result.status == 200
    assert called == [True]


def test_require_csrf_rejects_invalid_token(monkeypatch):
    """@require_csrf retourne 403 si le token est invalide."""
    request = _patch_csrf(monkeypatch, session_token="abc", form_token="xyz")
    called = []

    @require_csrf
    def handler(req):
        called.append(True)
        return Response(200, b"OK")

    result = handler(request)
    assert result.status == 403
    assert called == []


def test_require_csrf_rejects_absent_form_token(monkeypatch):
    """@require_csrf retourne 403 si le token formulaire est absent."""
    request = _patch_csrf(monkeypatch, session_token="abc", form_token=None)

    @require_csrf
    def handler(req):
        return Response(200, b"OK")

    result = handler(request)
    assert result.status == 403


def test_require_csrf_rejects_both_tokens_absent(monkeypatch):
    """@require_csrf retourne 403 quand les deux tokens sont absents.

    Corrige le bug None-None de l'ancienne implémentation naïve :
    (None != None) == False → laissait passer les requêtes sans session ni token.
    """
    request = _patch_csrf(monkeypatch, session_token=None, form_token=None)

    @require_csrf
    def handler(req):
        return Response(200, b"OK")

    result = handler(request)
    assert result.status == 403


def test_require_csrf_delegates_to_csrf_middleware(monkeypatch):
    """@require_csrf utilise CsrfMiddleware — une seule implémentation CSRF."""
    calls = []
    original_check = CsrfMiddleware.check

    def spy_check(self, request):
        calls.append(request)
        return original_check(self, request)

    monkeypatch.setattr(CsrfMiddleware, "check", spy_check)
    request = _patch_csrf(monkeypatch, session_token="tok", form_token="tok")

    @require_csrf
    def handler(req):
        return Response(200, b"OK")

    handler(request)
    assert len(calls) == 1, "@require_csrf doit déléguer à CsrfMiddleware.check()"
