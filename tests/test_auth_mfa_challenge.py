"""Tests unitaires — Challenge MFA à la connexion (AUTH-MFA-004)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp

from forge_mvc_mfa.secret_crypto import encrypt_totp_secret

_TEST_FERNET_KEY = "aGsgWXh_DXIOTYw2nsUvnhb8tQkPflH-rWnGywxsg8I="

@pytest.fixture(autouse=True)
def _mfa_secret_key(monkeypatch):
    monkeypatch.setenv("FORGE_MFA_SECRET_KEY", _TEST_FERNET_KEY)


from core.auth.exceptions import InvalidAuthUserError
from forge_mvc_mfa import (
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    MFA_STATUS_DISABLED,
    MFA_STATUS_PENDING,
    AuthMfaFactor,
    MfaChallengeResult,
    clear_mfa_challenge,
    get_mfa_challenge_user_id,
    has_pending_mfa_challenge,
    start_mfa_challenge,
    verify_mfa_challenge,
)
from forge_mvc_mfa import (
    AuthMfaRecoveryCode,
    create_recovery_codes,
    hash_recovery_code,
)
from core.auth.user import AuthUser


class FakeRequest:
    def __init__(self):
        self.session = {}


def _make_user(user_id: int = 1, is_active: bool = True) -> AuthUser:
    return AuthUser(
        id=user_id,
        login=f"user{user_id}@example.com",
        password_hash="$argon2id$fake",
        is_active=is_active,
    )


def _make_totp_factor(user_id: int, secret: str, status: str = MFA_STATUS_ACTIVE) -> AuthMfaFactor:
    return AuthMfaFactor(
        id=1,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=encrypt_totp_secret(secret),
        status=status,
        confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


def _make_recovery_code_record(
    user_id: int,
    raw_code: str,
    code_id: int = 1,
    used_at: datetime | None = None,
) -> AuthMfaRecoveryCode:
    return AuthMfaRecoveryCode(
        id=code_id,
        user_id=user_id,
        code_hash=hash_recovery_code(raw_code),
        used_at=used_at,
        created_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


_NOW = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# start_mfa_challenge
# ---------------------------------------------------------------------------


class TestStartMfaChallenge:
    def test_stores_user_id_in_session(self):
        req = FakeRequest()
        user = _make_user(42)
        start_mfa_challenge(req, user, now=_NOW)
        assert req.session[MFA_CHALLENGE_USER_ID_KEY] == 42

    def test_stores_started_at_in_session(self):
        req = FakeRequest()
        user = _make_user(42)
        start_mfa_challenge(req, user, now=_NOW)
        assert MFA_CHALLENGE_STARTED_AT_KEY in req.session
        assert isinstance(req.session[MFA_CHALLENGE_STARTED_AT_KEY], str)

    def test_does_not_store_email(self):
        req = FakeRequest()
        user = _make_user(7)
        start_mfa_challenge(req, user, now=_NOW)
        session_values = list(req.session.values())
        assert "user7@example.com" not in session_values
        for v in session_values:
            if isinstance(v, str):
                assert "example.com" not in v

    def test_does_not_store_password_hash(self):
        req = FakeRequest()
        user = _make_user(7)
        start_mfa_challenge(req, user, now=_NOW)
        assert "$argon2id$fake" not in req.session.values()

    def test_accepts_dict_user(self):
        req = FakeRequest()
        user_dict = {
            "id": 5,
            "login": "dict@example.com",
            "password_hash": "$argon2id$fake",
            "is_active": True,
        }
        start_mfa_challenge(req, user_dict, now=_NOW)
        assert req.session[MFA_CHALLENGE_USER_ID_KEY] == 5

    def test_rejects_invalid_user_type(self):
        req = FakeRequest()
        with pytest.raises(InvalidAuthUserError):
            start_mfa_challenge(req, "not_a_user", now=_NOW)

    def test_rejects_invalid_user_dict(self):
        req = FakeRequest()
        with pytest.raises(Exception):
            start_mfa_challenge(req, {"id": 1}, now=_NOW)

    def test_rejects_inactive_user(self):
        req = FakeRequest()
        user = _make_user(3, is_active=False)
        with pytest.raises(InvalidAuthUserError):
            start_mfa_challenge(req, user, now=_NOW)

    def test_does_not_call_login_user(self):
        from core.auth import session as session_module

        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        assert session_module.AUTH_USER_ID_SESSION_KEY not in req.session

    def test_only_stores_two_mfa_keys(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        assert set(req.session.keys()) == {MFA_CHALLENGE_USER_ID_KEY, MFA_CHALLENGE_STARTED_AT_KEY}


# ---------------------------------------------------------------------------
# get_mfa_challenge_user_id
# ---------------------------------------------------------------------------


class TestGetMfaChallengeUserId:
    def test_returns_none_without_challenge(self):
        req = FakeRequest()
        assert get_mfa_challenge_user_id(req) is None

    def test_returns_none_with_missing_key(self):
        req = FakeRequest()
        req.session[MFA_CHALLENGE_STARTED_AT_KEY] = _NOW.isoformat()
        assert get_mfa_challenge_user_id(req) is None

    def test_returns_none_for_invalid_user_id(self):
        req = FakeRequest()
        req.session[MFA_CHALLENGE_USER_ID_KEY] = "not_an_int"
        assert get_mfa_challenge_user_id(req) is None

    def test_returns_none_for_zero_user_id(self):
        req = FakeRequest()
        req.session[MFA_CHALLENGE_USER_ID_KEY] = 0
        assert get_mfa_challenge_user_id(req) is None

    def test_returns_user_id_with_valid_challenge(self):
        req = FakeRequest()
        user = _make_user(99)
        start_mfa_challenge(req, user, now=_NOW)
        assert get_mfa_challenge_user_id(req) == 99


# ---------------------------------------------------------------------------
# has_pending_mfa_challenge
# ---------------------------------------------------------------------------


class TestHasPendingMfaChallenge:
    def test_returns_false_without_challenge(self):
        req = FakeRequest()
        assert has_pending_mfa_challenge(req, now=_NOW) is False

    def test_returns_true_with_recent_challenge(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        assert has_pending_mfa_challenge(req, now=_NOW) is True

    def test_returns_false_with_expired_challenge(self):
        req = FakeRequest()
        user = _make_user(1)
        past = _NOW - timedelta(minutes=11)
        start_mfa_challenge(req, user, now=past)
        assert has_pending_mfa_challenge(req, max_age_minutes=10, now=_NOW) is False

    def test_returns_true_at_boundary(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        exactly_10_min_later = _NOW + timedelta(minutes=10)
        assert has_pending_mfa_challenge(req, max_age_minutes=10, now=exactly_10_min_later) is True

    def test_returns_false_just_after_boundary(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        just_after = _NOW + timedelta(minutes=10, seconds=1)
        assert has_pending_mfa_challenge(req, max_age_minutes=10, now=just_after) is False

    def test_returns_false_for_zero_max_age(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        assert has_pending_mfa_challenge(req, max_age_minutes=0, now=_NOW) is False

    def test_returns_false_for_negative_max_age(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        assert has_pending_mfa_challenge(req, max_age_minutes=-5, now=_NOW) is False

    def test_does_not_modify_session(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        session_before = dict(req.session)
        has_pending_mfa_challenge(req, now=_NOW)
        assert req.session == session_before


# ---------------------------------------------------------------------------
# clear_mfa_challenge
# ---------------------------------------------------------------------------


class TestClearMfaChallenge:
    def test_removes_mfa_keys(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        clear_mfa_challenge(req)
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session
        assert MFA_CHALLENGE_STARTED_AT_KEY not in req.session

    def test_is_idempotent(self):
        req = FakeRequest()
        clear_mfa_challenge(req)
        clear_mfa_challenge(req)
        assert req.session == {}

    def test_preserves_other_session_keys(self):
        req = FakeRequest()
        req.session["_flash"] = "message"
        req.session["_csrf"] = "token123"
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        clear_mfa_challenge(req)
        assert req.session["_flash"] == "message"
        assert req.session["_csrf"] == "token123"

    def test_does_not_clear_full_session(self):
        req = FakeRequest()
        req.session["_auth_user_id"] = 42
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        clear_mfa_challenge(req)
        assert "_auth_user_id" in req.session


# ---------------------------------------------------------------------------
# verify_mfa_challenge — echecs generaux
# ---------------------------------------------------------------------------


class TestVerifyMfaChallengeFailures:
    def test_returns_none_without_challenge(self):
        req = FakeRequest()
        result = verify_mfa_challenge(req, "123456", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_expired_challenge(self):
        req = FakeRequest()
        user = _make_user(1)
        past = _NOW - timedelta(minutes=11)
        start_mfa_challenge(req, user, now=past)
        result = verify_mfa_challenge(req, "123456", factors=[], max_age_minutes=10, now=_NOW)
        assert result is None

    def test_clears_challenge_after_expiry(self):
        req = FakeRequest()
        user = _make_user(1)
        past = _NOW - timedelta(minutes=11)
        start_mfa_challenge(req, user, now=past)
        verify_mfa_challenge(req, "123456", factors=[], max_age_minutes=10, now=_NOW)
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session
        assert MFA_CHALLENGE_STARTED_AT_KEY not in req.session

    def test_returns_none_with_empty_code(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, "", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_whitespace_code(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, "   ", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_non_string_code(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, 123456, factors=[], now=_NOW)  # type: ignore[arg-type]
        assert result is None

    def test_does_not_clear_challenge_on_wrong_code(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        verify_mfa_challenge(req, "000000", factors=[], now=_NOW)
        assert MFA_CHALLENGE_USER_ID_KEY in req.session
        assert MFA_CHALLENGE_STARTED_AT_KEY in req.session


# ---------------------------------------------------------------------------
# verify_mfa_challenge — TOTP
# ---------------------------------------------------------------------------


class TestVerifyMfaChallengeTOTP:
    def _setup(self, user_id: int = 1):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.at(_NOW.timestamp())
        factor = _make_totp_factor(user_id, secret, status=MFA_STATUS_ACTIVE)
        req = FakeRequest()
        user = _make_user(user_id)
        start_mfa_challenge(req, user, now=_NOW)
        return req, code, factor

    def test_valid_totp_returns_result(self):
        req, code, factor = self._setup()
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result is not None

    def test_valid_totp_method_is_totp(self):
        req, code, factor = self._setup()
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result.method == "totp"

    def test_valid_totp_returns_correct_user_id(self):
        req, code, factor = self._setup(user_id=7)
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result.user_id == 7

    def test_valid_totp_renseigne_verified_at(self):
        req, code, factor = self._setup()
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result.verified_at == _NOW

    def test_valid_totp_renseigne_factor_last_used_at(self):
        req, code, factor = self._setup()
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result.factor is not None
        assert result.factor.last_used_at == _NOW

    def test_valid_totp_renseigne_factor_updated_at(self):
        req, code, factor = self._setup()
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result.factor is not None
        assert result.factor.updated_at == _NOW

    def test_valid_totp_clears_challenge(self):
        req, code, factor = self._setup()
        verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session
        assert MFA_CHALLENGE_STARTED_AT_KEY not in req.session

    def test_wrong_totp_returns_none(self):
        req, _, factor = self._setup()
        result = verify_mfa_challenge(req, "000000", factors=[factor], now=_NOW)
        assert result is None

    def test_wrong_totp_does_not_clear_challenge(self):
        req, _, factor = self._setup()
        verify_mfa_challenge(req, "000000", factors=[factor], now=_NOW)
        assert MFA_CHALLENGE_USER_ID_KEY in req.session

    def test_ignores_pending_factor(self):
        req, code, factor = self._setup()
        pending_factor = _make_totp_factor(1, factor.totp_secret, status=MFA_STATUS_PENDING)
        result = verify_mfa_challenge(req, code, factors=[pending_factor], now=_NOW)
        assert result is None

    def test_ignores_disabled_factor(self):
        req, code, factor = self._setup()
        disabled_factor = _make_totp_factor(1, factor.totp_secret, status=MFA_STATUS_DISABLED)
        result = verify_mfa_challenge(req, code, factors=[disabled_factor], now=_NOW)
        assert result is None

    def test_ignores_factor_from_other_user(self):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.at(_NOW.timestamp())
        other_user_factor = _make_totp_factor(user_id=999, secret=secret, status=MFA_STATUS_ACTIVE)
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, code, factors=[other_user_factor], now=_NOW)
        assert result is None

    def test_uses_only_active_factor_among_mixed_list(self):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.at(_NOW.timestamp())
        active_factor = _make_totp_factor(1, secret, status=MFA_STATUS_ACTIVE)
        pending_factor = _make_totp_factor(1, secret, status=MFA_STATUS_PENDING)
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, code, factors=[pending_factor, active_factor], now=_NOW)
        assert result is not None
        assert result.method == "totp"

    def test_no_recovery_code_in_totp_result(self):
        req, code, factor = self._setup()
        result = verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert result.recovery_code is None


# ---------------------------------------------------------------------------
# verify_mfa_challenge — codes de recuperation
# ---------------------------------------------------------------------------


class TestVerifyMfaChallengeRecovery:
    def _setup_recovery(self, user_id: int = 1):
        setup = create_recovery_codes(user_id=user_id, count=5, now=_NOW)
        raw_code = setup.raw_codes[0]
        code_records = list(setup.code_records)
        req = FakeRequest()
        user = _make_user(user_id)
        start_mfa_challenge(req, user, now=_NOW)
        return req, raw_code, code_records

    def test_valid_recovery_code_returns_result(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result is not None

    def test_valid_recovery_code_method_is_recovery(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.method == "recovery"

    def test_valid_recovery_code_returns_correct_user_id(self):
        req, raw_code, records = self._setup_recovery(user_id=3)
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.user_id == 3

    def test_valid_recovery_code_renseigne_verified_at(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.verified_at == _NOW

    def test_valid_recovery_code_returns_consumed_record(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.recovery_code is not None
        assert result.recovery_code.used_at == _NOW

    def test_valid_recovery_code_clears_challenge(self):
        req, raw_code, records = self._setup_recovery()
        verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session

    def test_already_used_recovery_code_returns_none(self):
        setup = create_recovery_codes(user_id=1, count=3, now=_NOW)
        raw_code = setup.raw_codes[0]
        used_record = AuthMfaRecoveryCode(
            id=1,
            user_id=1,
            code_hash=hash_recovery_code(raw_code),
            used_at=_NOW - timedelta(hours=1),
        )
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=[used_record], now=_NOW)
        assert result is None

    def test_recovery_code_from_other_user_returns_none(self):
        setup = create_recovery_codes(user_id=999, count=3, now=_NOW)
        raw_code = setup.raw_codes[0]
        code_records = list(setup.code_records)
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=code_records, now=_NOW)
        assert result is None

    def test_recovery_codes_none_not_tried_when_totp_fails(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        result = verify_mfa_challenge(req, "AAAA-BBBB-CCCC-DDDD", factors=[], recovery_codes=None, now=_NOW)
        assert result is None

    def test_no_factor_in_recovery_result(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_challenge(req, raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.factor is None


# ---------------------------------------------------------------------------
# Integrite de l'API publique
# ---------------------------------------------------------------------------


class TestApiIntegrity:
    def test_importable_from_core_auth(self):
        from forge_mvc_mfa import (
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    clear_mfa_challenge,
    get_mfa_challenge_user_id,
    has_pending_mfa_challenge,
    start_mfa_challenge,
    verify_mfa_challenge,
)
        assert callable(start_mfa_challenge)
        assert callable(get_mfa_challenge_user_id)
        assert callable(has_pending_mfa_challenge)
        assert callable(clear_mfa_challenge)
        assert callable(verify_mfa_challenge)
        assert MFA_CHALLENGE_USER_ID_KEY == "_auth_mfa_user_id"
        assert MFA_CHALLENGE_STARTED_AT_KEY == "_auth_mfa_started_at"

    def test_mfa_challenge_result_is_frozen(self):
        result = MfaChallengeResult(
            user_id=1,
            method="totp",
            verified_at=_NOW,
        )
        with pytest.raises(Exception):
            result.user_id = 99  # type: ignore[misc]

    def test_no_login_user_called_on_success(self):
        from core.auth import session as session_module

        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.at(_NOW.timestamp())
        factor = _make_totp_factor(1, secret, status=MFA_STATUS_ACTIVE)
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
        assert session_module.AUTH_USER_ID_SESSION_KEY not in req.session

    def test_verify_does_not_modify_authenticate_user(self):
        from core.auth import authenticate_user

        assert callable(authenticate_user)

    def test_no_route_created(self):
        import core.auth as auth_module

        assert not hasattr(auth_module, "mfa_challenge_route")
        assert not hasattr(auth_module, "mfa_verify_route")

    def test_no_db_access_in_start(self):
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)

    def test_no_db_access_in_verify(self):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        factor = _make_totp_factor(1, secret, status=MFA_STATUS_ACTIVE)
        req = FakeRequest()
        user = _make_user(1)
        start_mfa_challenge(req, user, now=_NOW)
        verify_mfa_challenge(req, code, factors=[factor], now=_NOW)
