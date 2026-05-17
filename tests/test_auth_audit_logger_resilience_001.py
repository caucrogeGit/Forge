"""Tests AUTH-AUDIT-LOGGER-RESILIENCE-001 — resilience du logger d'audit auth.

Un echec du logger d'audit auth ne doit pas casser un flux applicatif critique.

Verifie que :
- un logger Python defaillant ne propage pas d'exception via safe_log_auth_event ;
- safe_log_auth_event retourne False et incremente le compteur si le logger echoue ;
- les evenements MFA et role nommes dans core/auth/audit.py sont acceptes ;
- les cles sensibles (password, token, secret...) sont filtrees des metadonnees ;
- core/auth/audit.py ne depend pas des opt-ins (forge_mvc_mfa, forge_mvc_rbac, pyotp).
"""
from __future__ import annotations

import logging
from pathlib import Path
from unittest.mock import patch

import pytest

from core.auth.audit import (
    AUTH_EVENT_LOGIN_FAILED,
    AUTH_EVENT_LOGIN_SUCCESS,
    AUTH_EVENT_LOGOUT,
    AUTH_EVENT_MFA_CHALLENGE_FAILED,
    AUTH_EVENT_MFA_CHALLENGE_SUCCESS,
    AUTH_EVENT_MFA_RATE_LIMITED,
    AUTH_EVENT_MFA_REVALIDATION_FAILED,
    AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH,
    AUTH_EVENT_MFA_REVALIDATION_SUCCESS,
    AUTH_EVENT_MFA_REQUIRED,
    AUTH_EVENT_USER_ROLE_ADDED,
    AUTH_EVENT_USER_ROLE_REMOVED,
    get_audit_failure_count,
    safe_log_auth_event,
    sanitize_auth_audit_metadata,
)

PROJECT_ROOT = Path(__file__).parent.parent

_AUDIT_LOGGER = logging.getLogger("forge.auth.audit")


class TestLoggerDefaillantNeBloquesPas:
    """Un logger Python defaillant ne bloque pas le flux appelant."""

    def test_logger_os_error_returns_false(self):
        with patch.object(_AUDIT_LOGGER, "log", side_effect=OSError("disk full")):
            result = safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
        assert result is False

    def test_logger_runtime_error_returns_false(self):
        with patch.object(_AUDIT_LOGGER, "log", side_effect=RuntimeError("handler crash")):
            result = safe_log_auth_event(AUTH_EVENT_LOGOUT, user_id=2)
        assert result is False

    def test_logger_down_does_not_propagate_exception(self):
        with patch.object(_AUDIT_LOGGER, "log", side_effect=OSError("disk full")):
            try:
                safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
            except Exception:
                pytest.fail("safe_log_auth_event ne doit jamais propager d'exception")

    def test_logger_down_increments_failure_count(self):
        with patch.object(_AUDIT_LOGGER, "log", side_effect=OSError("disk full")):
            safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
        assert get_audit_failure_count() == 1

    def test_multiple_failures_cumulated(self):
        with patch.object(_AUDIT_LOGGER, "log", side_effect=OSError("disk full")):
            safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
            safe_log_auth_event(AUTH_EVENT_LOGIN_FAILED, user_id=2)
        assert get_audit_failure_count() == 2

    def test_nominal_login_event_returns_true(self):
        result = safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1, ip_address="10.0.0.1")
        assert result is True
        assert get_audit_failure_count() == 0


class TestMfaEtRoleEventsAcceptes:
    """Les evenements MFA et role RBAC nommes dans le core sont acceptes par safe_log_auth_event."""

    @pytest.mark.parametrize("event_type", [
        AUTH_EVENT_MFA_REQUIRED,
        AUTH_EVENT_MFA_CHALLENGE_SUCCESS,
        AUTH_EVENT_MFA_CHALLENGE_FAILED,
        AUTH_EVENT_MFA_REVALIDATION_SUCCESS,
        AUTH_EVENT_MFA_REVALIDATION_FAILED,
        AUTH_EVENT_MFA_RATE_LIMITED,
        AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH,
        AUTH_EVENT_USER_ROLE_ADDED,
        AUTH_EVENT_USER_ROLE_REMOVED,
    ])
    def test_event_accepte_par_safe_log(self, event_type):
        result = safe_log_auth_event(event_type, user_id=1)
        assert result is True

    def test_mfa_challenge_failed_emis_au_niveau_warning(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="forge.auth.audit"):
            safe_log_auth_event(AUTH_EVENT_MFA_CHALLENGE_FAILED, user_id=1, ip_address="1.2.3.4")
        assert any(r.levelno >= logging.WARNING for r in caplog.records)

    def test_login_success_emis_au_niveau_info(self, caplog):
        with caplog.at_level(logging.DEBUG, logger="forge.auth.audit"):
            safe_log_auth_event(AUTH_EVENT_LOGIN_SUCCESS, user_id=1)
        assert any(r.levelno == logging.INFO for r in caplog.records)


class TestPayloadsSensiblesFiltres:
    """Les cles sensibles sont absentes des metadonnees sanitisees."""

    @pytest.mark.parametrize("sensitive_key", [
        "password",
        "password_hash",
        "token",
        "raw_token",
        "access_token",
        "refresh_token",
        "secret",
        "totp_secret",
        "recovery_code",
    ])
    def test_cle_sensible_supprimee(self, sensitive_key):
        result = sanitize_auth_audit_metadata({sensitive_key: "valeur_sensible", "ok": "safe"})
        assert sensitive_key not in result

    def test_cles_non_sensibles_preservees(self):
        meta = {"reason": "bad_password", "attempts": 3, "endpoint": "login"}
        result = sanitize_auth_audit_metadata(meta)
        assert result == meta

    def test_metadata_none_retourne_none(self):
        assert sanitize_auth_audit_metadata(None) is None


class TestNoCoreOptInDependency:
    """core/auth/audit.py ne depend pas des modules opt-in."""

    def _audit_src(self) -> str:
        return (PROJECT_ROOT / "core" / "auth" / "audit.py").read_text(encoding="utf-8")

    def test_no_forge_mvc_mfa_import(self):
        assert "forge_mvc_mfa" not in self._audit_src()

    def test_no_forge_mvc_rbac_import(self):
        assert "forge_mvc_rbac" not in self._audit_src()

    def test_no_pyotp_import(self):
        assert "pyotp" not in self._audit_src()
