"""
Tests SECURITY-AUTH-AUDIT-001 — Journalisation des événements auth.

Vérifie que core/auth/audit.log_auth_event() est appelé depuis
auth_controller.py et mfa_challenge_controller.py sur les événements
importants, sans jamais exposer de données sensibles dans les logs.
"""
from __future__ import annotations

import logging
from unittest.mock import patch, MagicMock

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")
import pyotp

from forge_mvc_mfa.secret_crypto import encrypt_totp_secret

_TEST_FERNET_KEY = "aGsgWXh_DXIOTYw2nsUvnhb8tQkPflH-rWnGywxsg8I="

@pytest.fixture(autouse=True)
def _mfa_secret_key(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _TEST_FERNET_KEY)


import core.forge as _forge
from core.auth.audit import (
    AUTH_EVENT_LOGIN_FAILED,
    AUTH_EVENT_LOGIN_SUCCESS,
    AUTH_EVENT_LOGOUT,
    AUTH_EVENT_MFA_CHALLENGE_FAILED,
    AUTH_EVENT_MFA_CHALLENGE_SUCCESS,
    AUTH_EVENT_USER_DISABLED,
    log_auth_event,
)
from forge_mvc_mfa import (
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    start_mfa_challenge,
)
from core.auth.user import AuthUser
from core.security.session import create_session, get_session
from core.templating.manager import template_manager
from integrations.jinja2.renderer import Jinja2Renderer
from mvc.controllers.auth_controller import AuthController
from mvc.controllers.mfa_challenge_controller import MfaChallengeController
from tests.fake_request import FakeRequest


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _views(tmp_path):
    """Crée les templates minimaux pour éviter les erreurs de rendu."""
    (tmp_path / "auth").mkdir()
    (tmp_path / "errors").mkdir()
    (tmp_path / "auth" / "login.html").write_text(
        "LOGIN csrf={{ csrf_token }} erreur={{ erreur }}", encoding="utf-8"
    )
    (tmp_path / "auth" / "mfa_challenge.html").write_text(
        "MFA csrf={{ csrf_token }} erreur={{ erreur }}", encoding="utf-8"
    )
    (tmp_path / "errors" / "403.html").write_text("403", encoding="utf-8")
    (tmp_path / "errors" / "429.html").write_text("429", encoding="utf-8")
    _forge._cfg["views_dir"] = str(tmp_path)
    template_manager.register(Jinja2Renderer(str(tmp_path)))
    yield


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_user(*, actif=1, uid=42, email="user@example.com"):
    return {
        "UtilisateurId": uid,
        "Login": "user@example.com",
        "PasswordHash": "$argon2id$fake",
        "Actif": actif,
        "Email": email,
        "Prenom": "Test",
        "Nom": "User",
        "roles": [],
    }


def _post_login(password="secret", user=None, *, ip="1.2.3.4"):
    """Simule POST /login avec un utilisateur mocké. Retourne (response, caplog)."""
    if user is None:
        user = _make_user()
    sid  = create_session()
    sess = get_session(sid)
    req  = FakeRequest(
        "POST", "/login",
        body={"login": user["Login"], "password": password,
              "csrf_token": sess["csrf_token"]},
        session_id=sid,
        ip=ip,
    )
    return req


def _post_logout(*, user_id=42, ip="1.2.3.4"):
    """Crée une session authentifiée et simule POST /logout."""
    from core.security.session import authenticate_session
    sid = create_session()
    utilisateur = _make_user(uid=user_id)
    nouveau_id = authenticate_session(sid, utilisateur)
    sess = get_session(nouveau_id)
    req = FakeRequest(
        "POST", "/logout",
        body={"csrf_token": sess["csrf_token"]},
        session_id=nouveau_id,
        ip=ip,
    )
    return req


# ── Tests log_auth_event() directement ───────────────────────────────────────

class TestLogAuthEventDirectement:

    def test_login_success_loggue_info(self, caplog):
        """login.success → niveau INFO dans forge.auth.audit."""
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1, ip_address="1.2.3.4")
        assert any("login.success" in r.message for r in caplog.records)
        assert any(r.levelno == logging.INFO for r in caplog.records
                   if "login.success" in r.message)

    def test_login_failed_loggue_warning(self, caplog):
        """login.failed → niveau WARNING dans forge.auth.audit."""
        with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_LOGIN_FAILED, ip_address="1.2.3.4")
        assert any("login.failed" in r.message for r in caplog.records)
        assert any(r.levelno == logging.WARNING for r in caplog.records
                   if "login.failed" in r.message)

    def test_logout_loggue_info(self, caplog):
        """logout → niveau INFO."""
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_LOGOUT, user_id=7, ip_address="5.6.7.8")
        assert any("logout" in r.message for r in caplog.records)

    def test_user_disabled_loggue_warning(self, caplog):
        """user.disabled → niveau WARNING."""
        with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_USER_DISABLED, user_id=3)
        assert any("user.disabled" in r.message for r in caplog.records)

    def test_mfa_challenge_failed_loggue_warning(self, caplog):
        """mfa.challenge.failed → niveau WARNING."""
        with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_MFA_CHALLENGE_FAILED, user_id=5)
        assert any("mfa.challenge.failed" in r.message for r in caplog.records)

    def test_mfa_challenge_success_loggue_info(self, caplog):
        """mfa.challenge.success → niveau INFO."""
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_MFA_CHALLENGE_SUCCESS, user_id=5)
        assert any("mfa.challenge.success" in r.message for r in caplog.records)

    def test_leve_sur_event_type_invalide(self):
        """log_auth_event avec event_type invalide lève InvalidAuthAuditEventError."""
        from core.auth.exceptions import InvalidAuthAuditEventError
        with pytest.raises(InvalidAuthAuditEventError):
            log_auth_event("")

    def test_password_jamais_dans_les_logs(self, caplog):
        """Le mot de passe n'apparaît jamais dans les logs d'audit."""
        with caplog.at_level(logging.DEBUG, logger="forge.auth.audit"):
            log_auth_event(
                AUTH_EVENT_LOGIN_FAILED,
                ip_address="1.2.3.4",
                metadata={"password": "secret123", "login": "user@example.com"},
            )
        for record in caplog.records:
            assert "secret123" not in record.message
            assert "secret123" not in str(record.args)

    def test_token_jamais_dans_les_logs(self, caplog):
        """Les tokens (access_token, raw_token…) n'apparaissent jamais dans les logs."""
        with caplog.at_level(logging.DEBUG, logger="forge.auth.audit"):
            log_auth_event(
                AUTH_EVENT_LOGIN_SUCCESS,
                user_id=1,
                metadata={"access_token": "tok-secret", "user": "test"},
            )
        for record in caplog.records:
            assert "tok-secret" not in record.message
            assert "tok-secret" not in str(record.args)

    def test_user_id_present_dans_log_success(self, caplog):
        """user_id apparaît dans le message de log success."""
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=42, ip_address="9.9.9.9")
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "42" in messages

    def test_ip_present_dans_log(self, caplog):
        """ip_address apparaît dans le message de log."""
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1, ip_address="10.0.0.1")
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "10.0.0.1" in messages


# ── Tests auth_controller.py — login ─────────────────────────────────────────

class TestAuthControllerLoginAudit:

    def test_login_success_genere_evenement_audit(self, caplog):
        """Login réussi → forge.auth.audit reçoit login.success à INFO."""
        user = _make_user()
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=True),
            patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
            patch("mvc.controllers.auth_controller.is_mfa_enabled", return_value=False),
            caplog.at_level(logging.INFO, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        login_success_records = [r for r in caplog.records if "login.success" in r.message]
        assert login_success_records, "login.success non journalisé"
        assert login_success_records[0].levelno == logging.INFO

    def test_login_success_loggue_user_id(self, caplog):
        """Login réussi → user_id dans le log."""
        user = _make_user(uid=99)
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=True),
            patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
            patch("mvc.controllers.auth_controller.is_mfa_enabled", return_value=False),
            caplog.at_level(logging.INFO, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "99" in messages

    def test_login_success_ne_loggue_pas_password(self, caplog):
        """Login réussi → le mot de passe n'apparaît pas dans les logs."""
        user = _make_user()
        req = _post_login(password="mon_secret_password", user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=True),
            patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
            patch("mvc.controllers.auth_controller.is_mfa_enabled", return_value=False),
            caplog.at_level(logging.DEBUG, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        for record in caplog.records:
            assert "mon_secret_password" not in record.getMessage()

    def test_login_echec_genere_login_failed(self, caplog):
        """Login échoué (mauvais mot de passe) → login.failed à WARNING."""
        user = _make_user()
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=False),
            caplog.at_level(logging.WARNING, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        failed_records = [r for r in caplog.records if "login.failed" in r.message]
        assert failed_records, "login.failed non journalisé"
        assert failed_records[0].levelno == logging.WARNING

    def test_login_user_inconnu_genere_login_failed(self, caplog):
        """Login avec utilisateur inconnu (None) → login.failed."""
        req = _post_login()
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=None),
            caplog.at_level(logging.WARNING, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        assert any("login.failed" in r.message for r in caplog.records)

    def test_login_compte_desactive_genere_user_disabled(self, caplog):
        """Login avec compte désactivé → user.disabled à WARNING (pas login.failed)."""
        user = _make_user(actif=0, uid=55)
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=False),
            caplog.at_level(logging.WARNING, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        disabled_records = [r for r in caplog.records if "user.disabled" in r.message]
        assert disabled_records, "user.disabled non journalisé pour compte désactivé"
        assert disabled_records[0].levelno == logging.WARNING

    def test_login_compte_desactive_ne_genere_pas_login_failed(self, caplog):
        """Login avec compte désactivé → user.disabled uniquement, pas login.failed."""
        user = _make_user(actif=0)
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=False),
            caplog.at_level(logging.DEBUG, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        assert not any("login.failed" in r.message for r in caplog.records)

    def test_login_success_ne_loggue_pas_hash(self, caplog):
        """Le password_hash n'apparaît jamais dans les logs."""
        user = _make_user()
        user["PasswordHash"] = "$argon2id$v=19$m=65536,t=3,p=4$SALTSALT$HASHHASHHASH"
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=True),
            patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
            patch("mvc.controllers.auth_controller.is_mfa_enabled", return_value=False),
            caplog.at_level(logging.DEBUG, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        for record in caplog.records:
            assert "HASHHASHHASH" not in record.getMessage()

    def test_login_ip_loggue_sur_echec(self, caplog):
        """L'IP est présente dans le log d'échec."""
        user = _make_user()
        req = _post_login(user=user, ip="192.168.1.99")
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=False),
            caplog.at_level(logging.WARNING, logger="forge.auth.audit"),
        ):
            AuthController.login(req)
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "192.168.1.99" in messages

    def test_comportement_auth_existant_preserve_sur_success(self):
        """Le branchement audit ne perturbe pas le comportement de redirection sur succès."""
        user = _make_user()
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=True),
            patch("mvc.controllers.auth_controller.get_active_mfa_factors", return_value=[]),
            patch("mvc.controllers.auth_controller.is_mfa_enabled", return_value=False),
        ):
            resp = AuthController.login(req)
        assert resp.status == 302
        assert resp.headers.get("Location") == "/"

    def test_comportement_auth_existant_preserve_sur_echec(self):
        """Le branchement audit ne perturbe pas le rendu du formulaire sur échec."""
        user = _make_user()
        req = _post_login(user=user)
        with (
            patch("mvc.controllers.auth_controller.get_user_by_login", return_value=user),
            patch("mvc.controllers.auth_controller._check_password", return_value=False),
        ):
            resp = AuthController.login(req)
        assert resp.status == 200
        assert b"erreur" in resp.body.lower() or b"LOGIN" in resp.body


# ── Tests auth_controller.py — logout ────────────────────────────────────────

class TestAuthControllerLogoutAudit:

    def test_logout_genere_evenement_audit(self, caplog):
        """Logout → forge.auth.audit reçoit logout à INFO."""
        req = _post_logout(user_id=42)
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            AuthController.logout(req)
        assert any("logout" in r.message for r in caplog.records)

    def test_logout_loggue_user_id(self, caplog):
        """Logout → user_id dans le log."""
        req = _post_logout(user_id=88)
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            AuthController.logout(req)
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "88" in messages

    def test_logout_loggue_ip(self, caplog):
        """Logout → IP dans le log."""
        req = _post_logout(ip="10.20.30.40")
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            AuthController.logout(req)
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "10.20.30.40" in messages

    def test_logout_niveau_info(self, caplog):
        """Logout → niveau INFO (pas WARNING)."""
        req = _post_logout()
        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            AuthController.logout(req)
        logout_records = [r for r in caplog.records if "logout" in r.message]
        assert logout_records
        assert logout_records[0].levelno == logging.INFO

    def test_comportement_logout_preserve(self):
        """Le branchement audit ne perturbe pas la redirection de logout."""
        req = _post_logout()
        resp = AuthController.logout(req)
        assert resp.status == 302
        assert "/login" in resp.headers.get("Location", "")


# ── Tests mfa_challenge_controller.py ────────────────────────────────────────

class TestMfaChallengeControllerAudit:
    """Tests de journalisation audit dans MfaChallengeController.verify()."""

    def _make_totp_factor(self, user_id: int = 1):
        secret = pyotp.random_base32()
        factor = AuthMfaFactor(
            id=1,
            user_id=user_id,
            factor_type=MFA_FACTOR_TOTP,
            status=MFA_STATUS_ACTIVE,
            totp_secret=encrypt_totp_secret(secret),
            last_used_at=None,
            created_at=None,
        )
        return factor, secret

    def _make_mfa_request(self, *, code="000000", user_id=1):
        session = {
            "csrf_token": "valid-token",
            "expires_at": 9999999999.0,
        }
        request = MagicMock()
        request.session = session
        request.body = {
            "csrf_token": ["valid-token"],
            "code": [code],
        }
        request.ip = "5.5.5.5"
        return request, user_id

    def test_mfa_challenge_success_journalise(self, caplog):
        """Code MFA valide → mfa.challenge.success journalisé à INFO."""
        factor, secret = self._make_totp_factor(user_id=10)
        valid_code = pyotp.TOTP(secret).now()
        request, user_id = self._make_mfa_request(code=valid_code, user_id=10)

        def _finalize(uid, sid, sess, req):
            return MagicMock(status=302)

        start_mfa_challenge(request, AuthUser(
            id=10, email="mfa@test.com",
            password_hash="$argon2id$fake", is_active=True,
        ))

        with caplog.at_level(logging.INFO, logger="forge.auth.audit"):
            MfaChallengeController.verify(
                request,
                _load_factors=lambda uid: [factor],
                _finalize_login=_finalize,
            )
        assert any("mfa.challenge.success" in r.message for r in caplog.records)

    def test_mfa_challenge_failed_journalise(self, caplog):
        """Code MFA invalide → mfa.challenge.failed journalisé à WARNING."""
        factor, secret = self._make_totp_factor(user_id=11)
        request, user_id = self._make_mfa_request(code="000000", user_id=11)

        start_mfa_challenge(request, AuthUser(
            id=11, email="mfa2@test.com",
            password_hash="$argon2id$fake", is_active=True,
        ))

        with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
            MfaChallengeController.verify(
                request,
                _load_factors=lambda uid: [factor],
            )
        failed_records = [r for r in caplog.records if "mfa.challenge.failed" in r.message]
        assert failed_records
        assert failed_records[0].levelno == logging.WARNING

    def test_mfa_challenge_failed_loggue_user_id(self, caplog):
        """Code MFA invalide → user_id dans le log."""
        factor, secret = self._make_totp_factor(user_id=77)
        request, _ = self._make_mfa_request(code="000000", user_id=77)

        start_mfa_challenge(request, AuthUser(
            id=77, email="mfa3@test.com",
            password_hash="$argon2id$fake", is_active=True,
        ))

        with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
            MfaChallengeController.verify(
                request,
                _load_factors=lambda uid: [factor],
            )
        messages = " ".join(r.getMessage() for r in caplog.records)
        assert "77" in messages

    def test_mfa_challenge_failed_ne_loggue_pas_code(self, caplog):
        """Le code MFA soumis n'apparaît pas dans les logs."""
        factor, secret = self._make_totp_factor(user_id=12)
        request, _ = self._make_mfa_request(code="123456", user_id=12)

        start_mfa_challenge(request, AuthUser(
            id=12, email="mfa4@test.com",
            password_hash="$argon2id$fake", is_active=True,
        ))

        with caplog.at_level(logging.DEBUG, logger="forge.auth.audit"):
            MfaChallengeController.verify(
                request,
                _load_factors=lambda uid: [factor],
            )
        for record in caplog.records:
            assert "123456" not in record.getMessage()

    def test_comportement_mfa_preserve_sur_echec(self):
        """Le branchement audit ne perturbe pas le rendu du formulaire MFA en cas d'échec."""
        factor, secret = self._make_totp_factor(user_id=13)
        request, _ = self._make_mfa_request(code="000000", user_id=13)

        start_mfa_challenge(request, AuthUser(
            id=13, email="mfa5@test.com",
            password_hash="$argon2id$fake", is_active=True,
        ))

        resp = MfaChallengeController.verify(
            request,
            _load_factors=lambda uid: [factor],
        )
        assert resp.status == 200


# ── safe_log_auth_event silencieux sans traceback dans le message ─────────────

class TestSafeLogAuditSilencieux:

    def test_pas_de_traceback_dans_le_message_de_warning(self, caplog):
        """safe_log_auth_event n'expose pas de traceback brut dans son message de warning."""
        from core.auth.audit import safe_log_auth_event
        with caplog.at_level(logging.WARNING, logger="forge.auth.audit"):
            # event_type vide lève InvalidAuthAuditEventError → captée par safe_log_auth_event
            safe_log_auth_event("")

        # Le warning est émis mais le message formaté ne contient pas de texte "Traceback" brut
        for record in caplog.records:
            assert "Traceback" not in record.getMessage()
            assert "InvalidAuthAuditEventError" not in record.getMessage()
