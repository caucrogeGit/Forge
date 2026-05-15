"""Tests SEC-CSRF-CONSTANT-TIME-001 : comparaison constant-time des tokens CSRF."""
from __future__ import annotations

from core.http.response import Response
from core.security.middleware import CsrfMiddleware


def _fake_html(template, status):
    return Response(status, "")


class _FakeRequest:
    def __init__(self, body=None, headers=None):
        self.body = body or {}
        self.headers = headers or {}


class TestCsrfConstantTime:
    def test_accepts_matching_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "abc123"})
        monkeypatch.setattr(mw, "_html", _fake_html)
        request = _FakeRequest(body={"csrf_token": ["abc123"]})
        assert CsrfMiddleware().check(request) is None

    def test_rejects_wrong_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "abc123"})
        monkeypatch.setattr(mw, "_html", _fake_html)
        request = _FakeRequest(body={"csrf_token": ["wrong"]})
        result = CsrfMiddleware().check(request)
        assert result is not None and result.status == 403

    def test_rejects_missing_provided_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "abc123"})
        monkeypatch.setattr(mw, "_html", _fake_html)
        request = _FakeRequest(body={})
        result = CsrfMiddleware().check(request)
        assert result is not None and result.status == 403

    def test_rejects_missing_session_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {})
        monkeypatch.setattr(mw, "_html", _fake_html)
        request = _FakeRequest(body={"csrf_token": ["abc123"]})
        result = CsrfMiddleware().check(request)
        assert result is not None and result.status == 403

    def test_uses_compare_digest(self):
        import inspect
        from core.security import middleware as mw
        source = inspect.getsource(mw.CsrfMiddleware.check)
        assert "compare_digest" in source
