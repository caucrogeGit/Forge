"""
Tests applicatifs du contrôleur d'authentification (mvc/controllers/auth_controller.py).

Ces tests valident le comportement de l'application, pas du framework :
login OK, login KO, CSRF, logout POST, rate limiting, route protégée.
"""
import pytest
from unittest.mock import patch

import core.forge as _forge
from core.security import session as _s
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.auth_controller import AuthController
from tests.fake_request import FakeRequest


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _views(tmp_path):
    """Crée les templates minimaux nécessaires au rendu des contrôleurs d'auth."""
    (tmp_path / "auth").mkdir()
    (tmp_path / "auth" / "partials").mkdir()
    (tmp_path / "errors").mkdir()
    (tmp_path / "auth" / "login.html").write_text(
        "LOGIN csrf={{ csrf_token }} erreur={{ erreur }}", encoding="utf-8"
    )
    (tmp_path / "auth" / "partials" / "erreur.html").write_text(
        "<span>{{ message }}</span>", encoding="utf-8"
    )
    (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
    (tmp_path / "errors" / "429.html").write_text("429", encoding="utf-8")
    _forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    yield
    _forge._cfg["views_dir"] = str(tmp_path)


_GOOD_USER = {
    "UtilisateurId": 1,
    "Login": "admin",
    "Actif": 1,
    "PasswordHash": "hash",
}


# ---------------------------------------------------------------------------
# login_form
# ---------------------------------------------------------------------------

class TestLoginForm:
    def test_retourne_200(self):
        req  = FakeRequest("GET", "/login")
        resp = AuthController.login_form(req)
        assert resp.status == 200

    def test_cree_une_session(self):
        req = FakeRequest("GET", "/login")
        AuthController.login_form(req)
        assert len(_s._sessions) >= 1

    def test_definit_le_cookie(self):
        req  = FakeRequest("GET", "/login")
        resp = AuthController.login_form(req)
        assert "session_id=" in resp.headers.get("Set-Cookie", "")

    def test_csrf_token_present_dans_le_rendu(self):
        req  = FakeRequest("GET", "/login")
        resp = AuthController.login_form(req)
        # Le template contient csrf={{ csrf_token }} — le token est injecté
        assert b"csrf=" in resp.body
        assert b"csrf= " not in resp.body   # pas vide


# ---------------------------------------------------------------------------
# login — succès
# ---------------------------------------------------------------------------

class TestLoginSuccess:
    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER)
    @patch("mvc.controllers.auth_controller.verifier_mot_de_passe", return_value=True)
    def test_redirige_vers_accueil(self, _vmdp, _gub):
        sid  = _s.creer_session()
        sess = _s.get_session(sid)
        req  = FakeRequest("POST", "/login",
                           body={"login": "admin", "password": "secret",
                                 "csrf_token": sess["csrf_token"]},
                           session_id=sid)
        resp = AuthController.login(req)
        assert resp.status == 302
        assert resp.headers.get("Location") == "/"

    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER)
    @patch("mvc.controllers.auth_controller.verifier_mot_de_passe", return_value=True)
    def test_rotation_session_id(self, _vmdp, _gub):
        sid  = _s.creer_session()
        sess = _s.get_session(sid)
        req  = FakeRequest("POST", "/login",
                           body={"login": "admin", "password": "secret",
                                 "csrf_token": sess["csrf_token"]},
                           session_id=sid)
        AuthController.login(req)
        # l'ancienne session a disparu (rotation)
        assert _s.get_session(sid) is None

    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER)
    @patch("mvc.controllers.auth_controller.verifier_mot_de_passe", return_value=True)
    def test_nouveau_cookie_dans_la_reponse(self, _vmdp, _gub):
        sid  = _s.creer_session()
        sess = _s.get_session(sid)
        req  = FakeRequest("POST", "/login",
                           body={"login": "admin", "password": "secret",
                                 "csrf_token": sess["csrf_token"]},
                           session_id=sid)
        resp = AuthController.login(req)
        assert "session_id=" in resp.headers.get("Set-Cookie", "")


# ---------------------------------------------------------------------------
# login — échec
# ---------------------------------------------------------------------------

class TestLoginFailure:
    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=None)
    def test_utilisateur_inconnu_retourne_200(self, _gub):
        sid  = _s.creer_session()
        sess = _s.get_session(sid)
        req  = FakeRequest("POST", "/login",
                           body={"login": "inconnu", "password": "x",
                                 "csrf_token": sess["csrf_token"]},
                           session_id=sid)
        resp = AuthController.login(req)
        assert resp.status == 200

    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER)
    @patch("mvc.controllers.auth_controller.verifier_mot_de_passe", return_value=False)
    def test_mauvais_mot_de_passe_retourne_200(self, _vmdp, _gub):
        sid  = _s.creer_session()
        sess = _s.get_session(sid)
        req  = FakeRequest("POST", "/login",
                           body={"login": "admin", "password": "mauvais",
                                 "csrf_token": sess["csrf_token"]},
                           session_id=sid)
        resp = AuthController.login(req)
        assert resp.status == 200

    def test_csrf_invalide_retourne_403(self):
        sid = _s.creer_session()
        req = FakeRequest("POST", "/login",
                          body={"login": "admin", "password": "x",
                                "csrf_token": "mauvais-token"},
                          session_id=sid)
        resp = AuthController.login(req)
        assert resp.status == 403

    def test_sans_session_retourne_403(self):
        req = FakeRequest("POST", "/login",
                          body={"login": "admin", "password": "x",
                                "csrf_token": "n'importe-quoi"})
        resp = AuthController.login(req)
        assert resp.status == 403


# ---------------------------------------------------------------------------
# Rate limiting
# ---------------------------------------------------------------------------

class TestRateLimiting:
    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=None)
    def test_429_apres_5_echecs(self, _gub):
        from core.security.hashing import enregistrer_tentative
        ip = "10.0.0.1"
        for _ in range(5):
            enregistrer_tentative(ip)
        req  = FakeRequest("POST", "/login",
                           body={"login": "x", "password": "x",
                                 "csrf_token": "y"},
                           ip=ip)
        resp = AuthController.login(req)
        assert resp.status == 429


# ---------------------------------------------------------------------------
# logout
# ---------------------------------------------------------------------------

class TestLogout:
    def _authentified_session(self):
        from core.security.session import authentifier_session
        sid  = _s.creer_session()
        sess = _s.get_session(sid)
        new_sid = authentifier_session(sid, _GOOD_USER)
        return new_sid, _s.get_session(new_sid)

    def test_logout_valide_redirige_vers_login(self):
        sid, sess = self._authentified_session()
        req  = FakeRequest("POST", "/logout",
                           body={"csrf_token": sess["csrf_token"]},
                           session_id=sid)
        resp = AuthController.logout(req)
        assert resp.status == 302
        assert resp.headers.get("Location") == "/login"

    def test_logout_detruit_la_session(self):
        sid, sess = self._authentified_session()
        req = FakeRequest("POST", "/logout",
                          body={"csrf_token": sess["csrf_token"]},
                          session_id=sid)
        AuthController.logout(req)
        assert _s.get_session(sid) is None

    def test_logout_efface_le_cookie(self):
        sid, sess = self._authentified_session()
        req  = FakeRequest("POST", "/logout",
                           body={"csrf_token": sess["csrf_token"]},
                           session_id=sid)
        resp = AuthController.logout(req)
        assert "Max-Age=0" in resp.headers.get("Set-Cookie", "")

    def test_logout_csrf_invalide_retourne_403(self):
        sid, _sess = self._authentified_session()
        req  = FakeRequest("POST", "/logout",
                           body={"csrf_token": "mauvais"},
                           session_id=sid)
        resp = AuthController.logout(req)
        assert resp.status == 403

    def test_logout_sans_session_retourne_403(self):
        req  = FakeRequest("POST", "/logout",
                           body={"csrf_token": "peu-importe"})
        resp = AuthController.logout(req)
        assert resp.status == 403
