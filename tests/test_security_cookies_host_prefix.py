"""Tests — SECURITY-COOKIES-HOST-PREFIX-001 : cookie de session préfixé __Host-.

Vérifie que :
- le cookie de session utilise le nom __Host-session_id ;
- Secure est présent ;
- Path=/ est présent ;
- aucun attribut Domain n'est émis ;
- HttpOnly est présent ;
- SameSite=Strict est présent ;
- get_session_id() lit correctement le cookie __Host-session_id ;
- le logout expire le cookie __Host-session_id (Max-Age=0) ;
- l'ancien nom session_id seul (sans préfixe) n'est pas accepté par get_session_id() ;
- la constante SESSION_COOKIE_NAME est exportée depuis core.security.session.
"""
from __future__ import annotations

import re
from types import SimpleNamespace
from unittest.mock import patch

import core.forge as _forge
import core.security.session as _s
from core.security.session import SESSION_COOKIE_NAME, get_session_id
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.auth_controller import AuthController
from tests.fake_request import FakeRequest

_GOOD_USER = {
    "UtilisateurId": 1,
    "Login": "admin",
    "Actif": 1,
    "PasswordHash": "$argon2id$v=19$m=65536$fakehash",
    "Prenom": "Alice",
    "Nom": "Martin",
    "Email": "alice@example.com",
    "roles": ["admin"],
}

_COOKIE_RE = re.compile(r"^[0-9a-f]{64}$")


import pytest


@pytest.fixture(autouse=True)
def _views(tmp_path):
    (tmp_path / "auth").mkdir()
    (tmp_path / "errors").mkdir()
    (tmp_path / "auth" / "login.html").write_text(
        "LOGIN csrf={{ csrf_token }}", encoding="utf-8"
    )
    (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
    (tmp_path / "errors" / "429.html").write_text("429", encoding="utf-8")
    old = _forge._cfg["views_dir"]
    _forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    yield
    _forge._cfg["views_dir"] = old


# ---------------------------------------------------------------------------
# Constante SESSION_COOKIE_NAME
# ---------------------------------------------------------------------------

class TestConstanteCookieName:
    def test_constante_existe(self):
        assert SESSION_COOKIE_NAME is not None

    def test_constante_commence_par_host_prefix(self):
        assert SESSION_COOKIE_NAME.startswith("__Host-")

    def test_constante_vaut_host_session_id(self):
        assert SESSION_COOKIE_NAME == "__Host-session_id"


# ---------------------------------------------------------------------------
# Cookie émis par GET /login — login_form
# ---------------------------------------------------------------------------

class TestCookieHostPrefixLoginForm:
    def _resp(self):
        return AuthController.login_form(FakeRequest("GET", "/login"))

    def test_cookie_utilise_host_prefix(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "__Host-session_id=" in cookie

    def test_cookie_contient_secure(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Secure" in cookie

    def test_cookie_contient_path_racine(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Path=/" in cookie

    def test_cookie_sans_domain(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Domain=" not in cookie

    def test_cookie_contient_httponly(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "HttpOnly" in cookie

    def test_cookie_contient_samesite_strict(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in cookie

    def test_cookie_valeur_est_hex_64(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        m = re.search(r"__Host-session_id=([0-9a-f]+)", cookie)
        assert m, "__Host-session_id doit contenir un token hex"
        assert _COOKIE_RE.match(m.group(1))

    def test_ancien_nom_session_id_non_utilise(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert not cookie.startswith("session_id=")


# ---------------------------------------------------------------------------
# Cookie émis par POST /login — succès
# ---------------------------------------------------------------------------

class TestCookieHostPrefixLoginSuccess:
    def _resp(self):
        sid = _s.create_session()
        sess = _s.get_session(sid)
        req = FakeRequest(
            "POST", "/login",
            body={"login": "admin", "password": "secret", "csrf_token": sess["csrf_token"]},
            session_id=sid,
        )
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER),
            patch("mvc.controllers.auth_controller._check_password", return_value=True),
            patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
        ):
            return AuthController.login(req)

    def test_cookie_utilise_host_prefix(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "__Host-session_id=" in cookie

    def test_cookie_sans_domain(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Domain=" not in cookie

    def test_cookie_contient_secure(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Secure" in cookie

    def test_cookie_contient_path_racine(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Path=/" in cookie


# ---------------------------------------------------------------------------
# Cookie logout — expiration __Host-session_id
# ---------------------------------------------------------------------------

class TestCookieHostPrefixLogout:
    def _resp(self):
        sid = _s.create_session()
        new_sid = _s.authenticate_session(sid, _GOOD_USER)
        sess = _s.get_session(new_sid)
        req = FakeRequest(
            "POST", "/logout",
            body={"csrf_token": sess["csrf_token"]},
            session_id=new_sid,
        )
        return AuthController.logout(req)

    def test_logout_cookie_utilise_host_prefix(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "__Host-session_id=" in cookie

    def test_logout_cookie_max_age_zero(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Max-Age=0" in cookie

    def test_logout_cookie_valeur_vide(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert re.search(r"__Host-session_id=\s*;", cookie)

    def test_logout_cookie_sans_domain(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Domain=" not in cookie


# ---------------------------------------------------------------------------
# get_session_id — lecture du cookie __Host-session_id
# ---------------------------------------------------------------------------

class TestGetSessionIdHostPrefix:
    def test_lit_host_session_id(self):
        sid = _s.create_session()
        req = SimpleNamespace(
            headers={"Cookie": f"__Host-session_id={sid}"},
            ip="127.0.0.1",
        )
        req.headers = type("H", (), {"get": lambda self, k, d="": req.headers.get(k, d)})()
        req.headers._d = {f"__Host-session_id={sid}": sid}
        # utiliser SimpleNamespace directement avec dict-like headers
        class _Req:
            headers = SimpleNamespace(get=lambda k, d="": f"__Host-session_id={sid}" if k == "Cookie" else d)
        assert get_session_id(_Req()) == sid

    def test_refuse_ancien_nom_session_id(self):
        sid = _s.create_session()
        class _Req:
            headers = SimpleNamespace(get=lambda k, d="": f"session_id={sid}" if k == "Cookie" else d)
        assert get_session_id(_Req()) is None

    def test_fake_request_utilise_host_prefix(self):
        sid = _s.create_session()
        req = FakeRequest("GET", "/", session_id=sid)
        assert get_session_id(req) == sid

    def test_fake_request_sans_session_retourne_none(self):
        req = FakeRequest("GET", "/")
        assert get_session_id(req) is None
