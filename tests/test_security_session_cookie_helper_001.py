"""Tests — SECURITY-SESSION-COOKIE-HELPER-001.

Verrouille le contrat du helper centralisé `core.security.cookies` :

  - le module est importable et expose `set_session_cookie` + `clear_session_cookie` ;
  - le header `Set-Cookie` produit contient les attributs de sécurité requis ;
  - les contraintes du préfixe `__Host-` sont vérifiées (Secure + Path=/) ;
  - les valeurs SameSite invalides sont refusées ;
  - les autres headers de la réponse ne sont pas écrasés ;
  - `clear_session_cookie` produit bien `Max-Age=0` avec valeur vide.

Aucun test ne migre les controllers — ce sera le ticket
SECURITY-SESSION-COOKIE-STARTERS-001.
"""
from __future__ import annotations

import pytest

from core.http.response import Response
from core.security.cookies import (
    clear_session_cookie,
    set_session_cookie,
)
from core.security.session import SESSION_COOKIE_NAME


def _attrs(set_cookie: str) -> dict[str, str | None]:
    """Décompose un header Set-Cookie en {attribut: valeur ou None pour les flags}."""
    out: dict[str, str | None] = {}
    parts = [p.strip() for p in set_cookie.split(";") if p.strip()]
    for i, part in enumerate(parts):
        if "=" in part:
            k, v = part.split("=", 1)
            key = k if i == 0 else k.lower()
            out[key] = v
        else:
            out[part.lower()] = None
    return out


# ── Importabilité ────────────────────────────────────────────────────────────


class TestModuleAndApi:
    def test_module_importable(self):
        import core.security.cookies as mod
        assert hasattr(mod, "set_session_cookie")
        assert hasattr(mod, "clear_session_cookie")


# ── Forme du Set-Cookie ──────────────────────────────────────────────────────


class TestSetSessionCookieDefaults:
    def test_contains_cookie_name_and_value(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc123")
        attrs = _attrs(response.headers["Set-Cookie"])
        assert attrs[SESSION_COOKIE_NAME] == "abc123"

    def test_contains_path_slash(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc123")
        attrs = _attrs(response.headers["Set-Cookie"])
        assert attrs["path"] == "/"

    def test_contains_httponly_flag(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc123")
        attrs = _attrs(response.headers["Set-Cookie"])
        assert "httponly" in attrs
        assert attrs["httponly"] is None

    def test_default_same_site_is_strict(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc123")
        attrs = _attrs(response.headers["Set-Cookie"])
        assert attrs["samesite"] == "Strict"

    def test_secure_present_by_default(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc123")
        attrs = _attrs(response.headers["Set-Cookie"])
        assert "secure" in attrs


class TestMaxAge:
    def test_no_max_age_by_default(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc")
        assert "Max-Age" not in response.headers["Set-Cookie"]

    def test_max_age_included_when_provided(self):
        response = Response(200, b"")
        set_session_cookie(response, "abc", max_age=3600)
        assert "Max-Age=3600" in response.headers["Set-Cookie"]


class TestSameSite:
    @pytest.mark.parametrize("value", ["Strict", "Lax", "None"])
    def test_accepts_valid_values(self, value):
        response = Response(200, b"")
        # None exige Secure=True, qui est le défaut.
        set_session_cookie(response, "abc", same_site=value)
        assert f"SameSite={value}" in response.headers["Set-Cookie"]

    @pytest.mark.parametrize("value", ["strict", "lax", "BAD", ""])
    def test_rejects_invalid_values(self, value):
        response = Response(200, b"")
        with pytest.raises(ValueError):
            set_session_cookie(response, "abc", same_site=value)

    def test_none_requires_secure(self):
        response = Response(200, b"")
        with pytest.raises(ValueError):
            set_session_cookie(
                response, "abc",
                same_site="None", secure=False,
                cookie_name="session_id",  # éviter le rappel __Host-
            )


class TestHostPrefixRules:
    def test_host_prefix_requires_secure(self):
        response = Response(200, b"")
        with pytest.raises(ValueError):
            set_session_cookie(response, "abc", secure=False)

    def test_host_prefix_requires_root_path(self):
        response = Response(200, b"")
        with pytest.raises(ValueError):
            set_session_cookie(response, "abc", path="/app")

    def test_non_host_cookie_allows_insecure(self):
        response = Response(200, b"")
        set_session_cookie(
            response, "abc",
            secure=False, cookie_name="session_id",
        )
        attrs = _attrs(response.headers["Set-Cookie"])
        assert "secure" not in attrs


class TestOtherHeadersPreserved:
    def test_existing_headers_not_overwritten(self):
        response = Response(200, b"", headers={"X-Custom": "yes"})
        set_session_cookie(response, "abc")
        assert response.headers["X-Custom"] == "yes"
        assert "Set-Cookie" in response.headers


# ── clear_session_cookie ────────────────────────────────────────────────────


class TestClearSessionCookie:
    def test_uses_empty_value_and_max_age_zero(self):
        response = Response(200, b"")
        clear_session_cookie(response)
        cookie = response.headers["Set-Cookie"]
        attrs = _attrs(cookie)
        assert attrs[SESSION_COOKIE_NAME] == ""
        assert "Max-Age=0" in cookie

    def test_keeps_security_attributes(self):
        response = Response(200, b"")
        clear_session_cookie(response)
        cookie = response.headers["Set-Cookie"]
        for token in ("Path=/", "HttpOnly", "SameSite=Strict", "Secure"):
            assert token in cookie, f"`{token}` manquant dans {cookie!r}"
