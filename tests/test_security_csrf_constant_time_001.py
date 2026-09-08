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
        monkeypatch.setattr(mw, "_error_page", _fake_html)
        request = _FakeRequest(body={"csrf_token": ["abc123"]})
        assert CsrfMiddleware().check(request) is None

    def test_rejects_wrong_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "abc123"})
        monkeypatch.setattr(mw, "_error_page", _fake_html)
        request = _FakeRequest(body={"csrf_token": ["wrong"]})
        result = CsrfMiddleware().check(request)
        assert result is not None and result.status == 403

    def test_rejects_missing_provided_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "abc123"})
        monkeypatch.setattr(mw, "_error_page", _fake_html)
        request = _FakeRequest(body={})
        result = CsrfMiddleware().check(request)
        assert result is not None and result.status == 403

    def test_rejects_missing_session_token(self, monkeypatch):
        from core.security import middleware as mw
        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {})
        monkeypatch.setattr(mw, "_error_page", _fake_html)
        request = _FakeRequest(body={"csrf_token": ["abc123"]})
        result = CsrfMiddleware().check(request)
        assert result is not None and result.status == 403

    def test_la_comparaison_reste_en_temps_constant(self):
        """La comparaison passe par `hmac.compare_digest`, où qu'elle vive.

        Le test exigeait le littéral `compare_digest` dans le corps de `check`.
        La comparaison a été déplacée dans un helper quand elle a cessé de
        porter sur des `str` : `hmac.compare_digest` refuse le non-ASCII en
        levant `TypeError`, et un jeton valant `é` rendait 500 au lieu de 403
        (`CORE-CSRF-TOKEN-NON-ASCII-001`).

        La fin visée n'est pas l'emplacement de l'appel, c'est qu'aucune
        comparaison naïve ne décide du refus. Le module est lu en entier, et
        l'absence d'un `==` sur les jetons est vérifiée à part.
        """
        import inspect

        from core.security import middleware as mw

        source = inspect.getsource(mw)

        assert "compare_digest" in source
        assert "provided == expected" not in source
        assert "expected == provided" not in source

    def test_le_jeton_non_ascii_est_refuse_pas_une_panne(self, monkeypatch):
        """Une entrée que n'importe qui envoie ne doit pas devenir une erreur 500."""
        from core.security import middleware as mw

        monkeypatch.setattr(mw, "get_session_id", lambda r: "sid")
        monkeypatch.setattr(mw, "get_session", lambda sid: {"csrf_token": "attendu"})
        monkeypatch.setattr(mw, "_error_page", _fake_html)

        for jeton in ("é", "🙂", "\udcff"):
            resultat = CsrfMiddleware().check(_FakeRequest(body={"csrf_token": [jeton]}))

            assert resultat is not None and resultat.status == 403, jeton
