"""Tests SEC-MFA-REVALIDATION-IDENTITY-001 — verification d'identite dans la revalidation MFA.

Verifie que verify_mfa_revalidation et mark_mfa_revalidated refusent silencieusement
toute tentative pour un user_id qui ne correspond pas a l'utilisateur authentifie
dans la session courante.
"""
from __future__ import annotations

from datetime import datetime, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp


from forge_mvc_mfa import (
    MFA_FACTOR_TOTP,
    MFA_REVALIDATION_USER_ID_KEY,
    MFA_STATUS_ACTIVE,
    AuthMfaFactor,
    has_recent_mfa_revalidation,
    mark_mfa_revalidated,
    verify_mfa_revalidation,
)
from forge_mvc_mfa.mfa import _session_user_matches

_NOW = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeRequest:
    def __init__(self):
        self.session = {}


def _req_unauthenticated() -> FakeRequest:
    return FakeRequest()


def _req_authenticated(user_id: int) -> FakeRequest:
    req = FakeRequest()
    req.session["authenticated"] = True
    req.session["user"] = {"id": user_id, "login": "test"}
    return req


def _active_totp_factor(user_id: int, factor_id: int = 1) -> tuple[AuthMfaFactor, str]:
    secret = pyotp.random_base32()
    factor = AuthMfaFactor(
        id=factor_id,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=secret,
        status=MFA_STATUS_ACTIVE,
        confirmed_at=_NOW,
    )
    return factor, secret


# ---------------------------------------------------------------------------
# _session_user_matches — le helper prive
# ---------------------------------------------------------------------------


class TestSessionUserMatchesHelper:
    def test_returns_false_sans_session(self):
        class NoSessionReq:
            pass
        assert _session_user_matches(NoSessionReq(), 1) is False

    def test_returns_false_session_non_authentifiee(self):
        req = _req_unauthenticated()
        assert _session_user_matches(req, 1) is False

    def test_returns_false_authentifie_sans_utilisateur(self):
        req = FakeRequest()
        req.session["authenticated"] = True
        assert _session_user_matches(req, 1) is False

    def test_returns_false_utilisateur_manque_id(self):
        req = FakeRequest()
        req.session["authenticated"] = True
        req.session["user"] = {"login": "alice"}
        assert _session_user_matches(req, 1) is False

    def test_returns_false_user_id_mismatch(self):
        req = _req_authenticated(100)
        assert _session_user_matches(req, 42) is False

    def test_returns_true_user_id_matches(self):
        req = _req_authenticated(42)
        assert _session_user_matches(req, 42) is True

    def test_returns_false_expected_user_id_zero(self):
        req = _req_authenticated(0)
        assert _session_user_matches(req, 0) is False

    def test_returns_false_expected_user_id_negative(self):
        req = _req_authenticated(1)
        assert _session_user_matches(req, -1) is False

    def test_returns_false_expected_user_id_bool(self):
        req = _req_authenticated(1)
        assert _session_user_matches(req, True) is False  # type: ignore[arg-type]

    def test_returns_false_session_utilisateur_non_dict(self):
        req = FakeRequest()
        req.session["authenticated"] = True
        req.session["user"] = 42
        assert _session_user_matches(req, 42) is False


# ---------------------------------------------------------------------------
# verify_mfa_revalidation — echecs d'identite
# ---------------------------------------------------------------------------


class TestVerifyMfaRevalidationIdentity:
    def test_refuses_session_non_authentifiee(self):
        factor, secret = _active_totp_factor(42)
        code = pyotp.TOTP(secret).now()
        req = _req_unauthenticated()
        result = verify_mfa_revalidation(req, 42, code, [factor], now=_NOW)
        assert result is None

    def test_refuses_session_autre_user(self):
        factor, secret = _active_totp_factor(42)
        code = pyotp.TOTP(secret).now()
        req = _req_authenticated(100)
        result = verify_mfa_revalidation(req, 42, code, [factor], now=_NOW)
        assert result is None

    def test_accepte_session_user_correct(self):
        factor, secret = _active_totp_factor(42)
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        req = _req_authenticated(42)
        result = verify_mfa_revalidation(req, 42, code, [factor], now=_NOW)
        assert result is not None
        assert result.user_id == 42

    def test_identite_incorrecte_ne_marque_pas_session(self):
        req = _req_authenticated(100)
        verify_mfa_revalidation(req, 42, "000000", [], now=_NOW)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session

    def test_identite_incorrecte_nincreamente_pas_rate_limit(self, monkeypatch):
        from core.auth import rate_limit as rl
        recorded = []
        monkeypatch.setattr(rl, "record_attempt", lambda *a, **kw: recorded.append(a))
        req = _req_unauthenticated()
        verify_mfa_revalidation(req, 42, "000000", [], now=_NOW)
        assert recorded == []

    def test_identite_incorrecte_emet_evenement_audit(self, monkeypatch):
        events: list[str] = []
        monkeypatch.setattr("core.auth.audit.log_auth_event",
                            lambda event_type, **kw: events.append(event_type))
        req = _req_authenticated(100)
        verify_mfa_revalidation(req, 42, "000000", [], now=_NOW)
        from core.auth.audit import AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH
        assert AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH in events

    def test_session_non_authentifiee_emet_audit(self, monkeypatch):
        events: list[str] = []
        monkeypatch.setattr("core.auth.audit.log_auth_event",
                            lambda event_type, **kw: events.append(event_type))
        req = _req_unauthenticated()
        verify_mfa_revalidation(req, 42, "000000", [], now=_NOW)
        from core.auth.audit import AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH
        assert AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH in events


# ---------------------------------------------------------------------------
# mark_mfa_revalidated — echecs d'identite
# ---------------------------------------------------------------------------


class TestMarkMfaRevalidatedIdentity:
    def test_noop_session_non_authentifiee(self):
        req = _req_unauthenticated()
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session

    def test_noop_session_autre_user(self):
        req = _req_authenticated(100)
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session

    def test_marque_quand_user_correct(self):
        req = _req_authenticated(42)
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        assert req.session[MFA_REVALIDATION_USER_ID_KEY] == 42

    def test_noop_ne_leve_pas(self):
        req = _req_unauthenticated()
        mark_mfa_revalidated(req, user_id=42, now=_NOW)

    def test_has_recent_revalidation_false_apres_noop(self):
        req = _req_unauthenticated()
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=42, now=_NOW) is False

    def test_has_recent_revalidation_true_quand_user_correct(self):
        req = _req_authenticated(42)
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=42, now=_NOW) is True


# ---------------------------------------------------------------------------
# Evenement audit importable
# ---------------------------------------------------------------------------


class TestAuditEventImportable:
    def test_event_importable_depuis_core_auth(self):
        from core.auth import AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH
        assert AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH == "mfa.revalidation.identity_mismatch"

    def test_event_dans_audit_event_types(self):
        from core.auth.audit import AUTH_AUDIT_EVENT_TYPES, AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH
        assert AUTH_EVENT_MFA_REVALIDATION_IDENTITY_MISMATCH in AUTH_AUDIT_EVENT_TYPES
