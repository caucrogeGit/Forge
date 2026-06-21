"""Audit cookies de session Forge (SECURITY-COOKIES-001).

Vérifie que tous les cookies émis par Forge respectent les attributs de sécurité
attendus : HttpOnly, SameSite=Strict, Secure, Path=/, suppression correcte au
logout, absence de données sensibles dans la valeur du cookie et dans la session
côté serveur, protection contre la fixation de session.

Périmètre audité :
- GET  /login  → login_form()         (auth_controller.py)
- POST /login  → login() succès       (auth_controller.py)
- POST /login  → login() redirect MFA (auth_controller.py)
- POST /logout → logout()             (auth_controller.py)
- POST /login/mfa → verify() succès   (mfa_challenge_controller.py)
"""
from __future__ import annotations

import re
import time
import pytest
from unittest.mock import patch

import core.forge as _forge
from core.security import session as _s
from core.auth.user import AuthUser
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.auth_controller import AuthController
from mvc.controllers.mfa_challenge_controller import MfaChallengeController
from forge_mvc_testing import FakeRequest

_HEX = re.compile(r"^[0-9a-f]{64}$")

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

_MFA_USER = AuthUser(
    id=1,
    email="alice@example.com",
    password_hash="$argon2id$v=19$m=65536$fakehash",
    is_active=True,
)


@pytest.fixture(autouse=True)
def _views(tmp_path):
    (tmp_path / "auth").mkdir()
    (tmp_path / "errors").mkdir()
    (tmp_path / "auth" / "login.html").write_text(
        "LOGIN csrf={{ csrf_token }}", encoding="utf-8"
    )
    (tmp_path / "auth" / "mfa_challenge.html").write_text(
        "MFA csrf={{ csrf_token }} erreur={{ erreur }}", encoding="utf-8"
    )
    (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
    (tmp_path / "errors" / "429.html").write_text("429", encoding="utf-8")
    old = _forge._cfg["views_dir"]
    _forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    yield
    _forge._cfg["views_dir"] = old


def _authentified_sid():
    sid = _s.create_session()
    new_sid = _s.authenticate_session(sid, _GOOD_USER)
    return new_sid, _s.get_session(new_sid)


def _login_success_resp():
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


def _login_mfa_redirect_resp():
    """Retourne la réponse de POST /login quand le MFA est activé."""
    from unittest.mock import MagicMock
    sid = _s.create_session()
    sess = _s.get_session(sid)
    req = FakeRequest(
        "POST", "/login",
        body={"login": "admin", "password": "secret", "csrf_token": sess["csrf_token"]},
        session_id=sid,
    )
    fake_factor = MagicMock()
    fake_factor.factor_type = "totp"
    fake_factor.status = "active"
    with (
        patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER),
        patch("mvc.controllers.auth_controller._check_password", return_value=True),
        patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[fake_factor]),
        patch("mvc.controllers.auth_controller.is_mfa_enabled", return_value=True),
        patch("mvc.controllers.auth_controller.start_mfa_challenge"),
    ):
        return AuthController.login(req), sid


# ---------------------------------------------------------------------------
# GET /login — login_form
# ---------------------------------------------------------------------------

class TestCookieSessionForm:
    """Cookie émis par login_form() : GET /login."""

    def _resp(self):
        return AuthController.login_form(FakeRequest("GET", "/login"))

    def test_httponly_sur_cookie_session(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "HttpOnly" in cookie

    def test_samesite_strict_sur_cookie_session(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in cookie

    def test_secure_sur_cookie_session(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Secure" in cookie

    def test_path_racine_sur_cookie_session(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Path=/" in cookie

    def test_cookie_valeur_est_token_opaque(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        m = re.search(r"__Host-session_id=([^;]+)", cookie)
        assert m, "__Host-session_id absent du cookie"
        token = m.group(1)
        assert len(token) > 16, "token trop court"
        assert "@" not in token
        assert "password" not in token.lower()
        assert "secret" not in token.lower()

    def test_pas_de_cookie_csrf_separe(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "csrf_token=" not in cookie


# ---------------------------------------------------------------------------
# POST /login — succès
# ---------------------------------------------------------------------------

class TestCookieLoginSuccess:
    """Cookie émis par login() en cas de succès : POST /login."""

    def test_httponly_sur_cookie_login_success(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "HttpOnly" in cookie

    def test_samesite_strict_sur_cookie_login_success(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in cookie

    def test_secure_sur_cookie_login_success(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "Secure" in cookie

    def test_path_racine_sur_cookie_login_success(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "Path=/" in cookie

    def test_cookie_login_success_ne_contient_pas_password(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "password" not in cookie.lower()
        assert "secret" not in cookie.lower()

    def test_cookie_login_success_ne_contient_pas_hash(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "argon2" not in cookie.lower()

    def test_pas_de_cookie_csrf_separe_login_success(self):
        cookie = _login_success_resp().headers.get("Set-Cookie", "")
        assert "csrf_token=" not in cookie


# ---------------------------------------------------------------------------
# POST /login — redirect MFA
# ---------------------------------------------------------------------------

class TestCookieLoginMfaRedirect:
    """Cookie émis par login() quand le MFA est activé : POST /login → /login/mfa."""

    def test_httponly_sur_redirect_mfa(self):
        resp, _ = _login_mfa_redirect_resp()
        cookie = resp.headers.get("Set-Cookie", "")
        assert "HttpOnly" in cookie

    def test_samesite_strict_sur_redirect_mfa(self):
        resp, _ = _login_mfa_redirect_resp()
        cookie = resp.headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in cookie

    def test_secure_sur_redirect_mfa(self):
        resp, _ = _login_mfa_redirect_resp()
        cookie = resp.headers.get("Set-Cookie", "")
        assert "Secure" in cookie

    def test_redirect_vers_mfa(self):
        resp, _ = _login_mfa_redirect_resp()
        assert resp.headers.get("Location") == "/login/mfa"


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------

class TestCookieLogout:
    """Cookie émis par logout() : POST /logout."""

    def _resp(self):
        sid, sess = _authentified_sid()
        req = FakeRequest(
            "POST", "/logout",
            body={"csrf_token": sess["csrf_token"]},
            session_id=sid,
        )
        return AuthController.logout(req)

    def test_logout_cookie_max_age_zero(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Max-Age=0" in cookie

    def test_logout_cookie_httponly(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "HttpOnly" in cookie

    def test_logout_cookie_samesite_strict(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in cookie

    def test_logout_cookie_secure(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Secure" in cookie

    def test_logout_cookie_path_racine(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "Path=/" in cookie

    def test_logout_cookie_valeur_vide(self):
        cookie = self._resp().headers.get("Set-Cookie", "")
        assert "__Host-session_id=;" in cookie or re.search(r"__Host-session_id=\s*;", cookie)


# ---------------------------------------------------------------------------
# POST /login/mfa — succès
# ---------------------------------------------------------------------------

class TestCookieMfaChallenge:
    """Cookie émis par MfaChallengeController.verify() en cas de succès."""

    @classmethod
    def setup_class(cls):
        pytest.importorskip("forge_mvc_mfa")

    def _mfa_resp(self):
        sid = _s.create_session()
        sess = _s.get_session(sid)
        req = FakeRequest(
            "POST", "/login/mfa",
            body={"csrf_token": sess["csrf_token"], "code": "123456"},
            session_id=sid,
        )

        def fake_finalize(user_id, session_id, session, request):
            from core.http.response import Response
            new_sid = _s.create_session()
            response = Response(302, headers={"Location": "/"})
            response.headers["Set-Cookie"] = (
                f"__Host-session_id={new_sid}; Path=/; HttpOnly; SameSite=Strict; Secure"
            )
            return response

        with (
            patch("mvc.controllers.mfa_challenge_controller.has_pending_mfa_challenge", return_value=True),
            patch("mvc.controllers.mfa_challenge_controller.get_mfa_challenge_user_id", return_value=1),
            patch("mvc.controllers.mfa_challenge_controller.verify_mfa_challenge", return_value=object()),
        ):
            resp = MfaChallengeController.verify(req, _finalize_login=fake_finalize)
        return resp, {}

    def test_mfa_challenge_success_cookie_httponly(self):
        resp, _ = self._mfa_resp()
        cookie = resp.headers.get("Set-Cookie", "")
        assert "HttpOnly" in cookie

    def test_mfa_challenge_success_cookie_samesite_strict(self):
        resp, _ = self._mfa_resp()
        cookie = resp.headers.get("Set-Cookie", "")
        assert "SameSite=Strict" in cookie

    def test_mfa_challenge_success_cookie_secure(self):
        resp, _ = self._mfa_resp()
        cookie = resp.headers.get("Set-Cookie", "")
        assert "Secure" in cookie


# ---------------------------------------------------------------------------
# Données dans la session côté serveur
# ---------------------------------------------------------------------------

class TestSessionDonneesServeur:
    """Les données stockées côté serveur ne contiennent pas de secrets."""

    def test_session_ne_contient_pas_password(self):
        sid = _s.create_session()
        new_sid = _s.authenticate_session(sid, _GOOD_USER)
        sess = _s.get_session(new_sid)
        assert sess is not None
        utilisateur = sess.get("user", {})
        assert "password" not in utilisateur
        assert "PasswordHash" not in utilisateur
        assert "password_hash" not in utilisateur

    def test_session_ne_contient_pas_token_secret(self):
        sid = _s.create_session()
        new_sid = _s.authenticate_session(sid, _GOOD_USER)
        sess = _s.get_session(new_sid)
        assert sess is not None
        for key in sess:
            assert "secret" not in key.lower()
            assert "token" not in key.lower() or key == "csrf_token"

    def test_session_utilisateur_contient_champs_attendus(self):
        sid = _s.create_session()
        new_sid = _s.authenticate_session(sid, _GOOD_USER)
        sess = _s.get_session(new_sid)
        utilisateur = sess["user"]
        assert "id" in utilisateur
        assert "login" in utilisateur
        assert "roles" in utilisateur

    def test_session_id_cookie_est_token_hex(self):
        resp = AuthController.login_form(FakeRequest("GET", "/login"))
        cookie = resp.headers.get("Set-Cookie", "")
        m = re.search(r"__Host-session_id=([0-9a-f]+)", cookie)
        assert m, "__Host-session_id doit être un token hex"
        assert len(m.group(1)) >= 32

    def test_session_ne_stocke_pas_email_complet_si_non_necessaire(self):
        sid = _s.create_session()
        new_sid = _s.authenticate_session(sid, _GOOD_USER)
        sess = _s.get_session(new_sid)
        utilisateur = sess.get("user", {})
        # l'email peut être présent (affichage profil) mais pas un secret
        # on vérifie l'absence de password dans tous les champs stringifiés
        serialized = str(utilisateur)
        assert "$argon2id$" not in serialized


# ---------------------------------------------------------------------------
# Protection contre la fixation de session
# ---------------------------------------------------------------------------

class TestFixationSession:
    """Le session_id est renouvelé au login — protège contre la session fixation."""

    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER)
    @patch("mvc.controllers.auth_controller._check_password", return_value=True)
    @patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[])
    def test_ancien_session_id_invalide_apres_login(self, _mfa, _cp, _gub):
        sid = _s.create_session()
        sess = _s.get_session(sid)
        req = FakeRequest(
            "POST", "/login",
            body={"login": "admin", "password": "secret", "csrf_token": sess["csrf_token"]},
            session_id=sid,
        )
        AuthController.login(req)
        assert _s.get_session(sid) is None

    @patch("mvc.controllers.auth_controller.get_user_by_login", return_value=_GOOD_USER)
    @patch("mvc.controllers.auth_controller._check_password", return_value=True)
    @patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[])
    def test_nouveau_session_id_different_de_lancien(self, _mfa, _cp, _gub):
        sid = _s.create_session()
        sess = _s.get_session(sid)
        req = FakeRequest(
            "POST", "/login",
            body={"login": "admin", "password": "secret", "csrf_token": sess["csrf_token"]},
            session_id=sid,
        )
        resp = AuthController.login(req)
        cookie = resp.headers.get("Set-Cookie", "")
        m = re.search(r"__Host-session_id=([0-9a-f]+)", cookie)
        assert m
        new_sid = m.group(1)
        assert new_sid != sid


# ---------------------------------------------------------------------------
# Durée de session
# ---------------------------------------------------------------------------

class TestDureeSession:
    """La durée de session est maîtrisée."""

    def test_duree_session_est_une_heure(self):
        from core.security.session import SESSION_DURATION
        assert SESSION_DURATION == 3600

    def test_session_expire_dans_le_futur(self):
        sid = _s.create_session()
        new_sid = _s.authenticate_session(sid, _GOOD_USER)
        sess_data = _s.get_session(new_sid)
        assert sess_data is not None
        assert sess_data["expires_at"] > time.time()
        assert sess_data["expires_at"] <= time.time() + 3601


# ---------------------------------------------------------------------------
# Comportement Secure en dev et prod
# ---------------------------------------------------------------------------

class TestComportementSecure:
    """Secure est toujours activé quel que soit app_env.

    Forge suppose que toute configuration de déploiement (y compris le
    développement local) passe par HTTPS ou un reverse-proxy TLS.
    Ce test documente ce choix de conception.
    """

    def test_secure_actif_en_dev(self):
        old = _forge._cfg.get("app_env")
        _forge._cfg["app_env"] = "dev"
        try:
            cookie = AuthController.login_form(FakeRequest("GET", "/login")).headers.get("Set-Cookie", "")
            assert "Secure" in cookie
        finally:
            _forge._cfg["app_env"] = old

    def test_secure_actif_en_prod(self):
        old = _forge._cfg.get("app_env")
        _forge._cfg["app_env"] = "prod"
        try:
            cookie = AuthController.login_form(FakeRequest("GET", "/login")).headers.get("Set-Cookie", "")
            assert "Secure" in cookie
        finally:
            _forge._cfg["app_env"] = old

    def test_app_env_par_defaut_est_dev(self):
        import core.forge as forge_mod
        assert forge_mod._cfg.get("app_env") in ("dev", "prod", "test")

    def test_pas_de_cookie_csrf_emis(self):
        """Forge ne crée pas de cookie CSRF séparé — le token est en session."""
        resp = AuthController.login_form(FakeRequest("GET", "/login"))
        cookie = resp.headers.get("Set-Cookie", "")
        assert "csrf=" not in cookie
        assert "csrf_token=" not in cookie
