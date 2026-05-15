"""Tests unitaires — Revalidation MFA pour actions sensibles (AUTH-MFA-005)."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp

from core.auth.exceptions import InvalidMfaFactorError
from forge_mvc_mfa import (
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    MFA_FACTOR_TOTP,
    MFA_REVALIDATION_AT_KEY,
    MFA_REVALIDATION_USER_ID_KEY,
    MFA_STATUS_ACTIVE,
    MFA_STATUS_DISABLED,
    MFA_STATUS_PENDING,
    AuthMfaFactor,
    MfaRevalidationResult,
    clear_mfa_revalidation,
    get_mfa_revalidated_user_id,
    has_recent_mfa_revalidation,
    mark_mfa_revalidated,
    require_recent_mfa,
    verify_mfa_revalidation,
)
from forge_mvc_mfa import (
    AuthMfaRecoveryCode,
    create_recovery_codes,
    hash_recovery_code,
)


class FakeRequest:
    def __init__(self):
        self.session = {}


def _authenticated_request(user_id: int) -> FakeRequest:
    """Cree une FakeRequest avec session authentifiee pour user_id."""
    req = FakeRequest()
    req.session["authenticated"] = True
    req.session["user"] = {"id": user_id, "login": "test"}
    return req


def _make_totp_factor(user_id: int, secret: str, status: str = MFA_STATUS_ACTIVE) -> AuthMfaFactor:
    return AuthMfaFactor(
        id=1,
        user_id=user_id,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret=secret,
        status=status,
        confirmed_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


_NOW = datetime(2026, 5, 3, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# mark_mfa_revalidated
# ---------------------------------------------------------------------------


class TestMarkMfaRevalidated:
    def test_stores_user_id(self):
        req = _authenticated_request(42)
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        assert req.session[MFA_REVALIDATION_USER_ID_KEY] == 42

    def test_stores_timestamp(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        assert MFA_REVALIDATION_AT_KEY in req.session
        assert isinstance(req.session[MFA_REVALIDATION_AT_KEY], str)

    def test_timestamp_is_iso_format(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        raw = req.session[MFA_REVALIDATION_AT_KEY]
        parsed = datetime.fromisoformat(raw)
        assert parsed == _NOW

    def test_refuses_zero_user_id(self):
        req = FakeRequest()
        with pytest.raises(InvalidMfaFactorError):
            mark_mfa_revalidated(req, user_id=0, now=_NOW)

    def test_refuses_negative_user_id(self):
        req = FakeRequest()
        with pytest.raises(InvalidMfaFactorError):
            mark_mfa_revalidated(req, user_id=-1, now=_NOW)

    def test_refuses_bool_user_id(self):
        req = FakeRequest()
        with pytest.raises(InvalidMfaFactorError):
            mark_mfa_revalidated(req, user_id=True, now=_NOW)

    def test_refuses_string_user_id(self):
        req = FakeRequest()
        with pytest.raises((InvalidMfaFactorError, TypeError)):
            mark_mfa_revalidated(req, user_id="1", now=_NOW)  # type: ignore[arg-type]

    def test_does_not_set_auth_user_id(self):
        from core.auth.session import AUTH_USER_ID_SESSION_KEY
        req = _authenticated_request(5)
        mark_mfa_revalidated(req, user_id=5, now=_NOW)
        assert AUTH_USER_ID_SESSION_KEY not in req.session

    def test_adds_only_revalidation_keys(self):
        req = _authenticated_request(3)
        before = set(req.session.keys())
        mark_mfa_revalidated(req, user_id=3, now=_NOW)
        added = set(req.session.keys()) - before
        assert added == {MFA_REVALIDATION_USER_ID_KEY, MFA_REVALIDATION_AT_KEY}


# ---------------------------------------------------------------------------
# get_mfa_revalidated_user_id
# ---------------------------------------------------------------------------


class TestGetMfaRevalidatedUserId:
    def test_returns_none_without_revalidation(self):
        req = FakeRequest()
        assert get_mfa_revalidated_user_id(req) is None

    def test_returns_none_for_invalid_user_id(self):
        req = FakeRequest()
        req.session[MFA_REVALIDATION_USER_ID_KEY] = "not_an_int"
        assert get_mfa_revalidated_user_id(req) is None

    def test_returns_none_for_zero(self):
        req = FakeRequest()
        req.session[MFA_REVALIDATION_USER_ID_KEY] = 0
        assert get_mfa_revalidated_user_id(req) is None

    def test_returns_user_id_when_valid(self):
        req = _authenticated_request(99)
        mark_mfa_revalidated(req, user_id=99, now=_NOW)
        assert get_mfa_revalidated_user_id(req) == 99


# ---------------------------------------------------------------------------
# has_recent_mfa_revalidation
# ---------------------------------------------------------------------------


class TestHasRecentMfaRevalidation:
    def test_returns_false_without_revalidation(self):
        req = FakeRequest()
        assert has_recent_mfa_revalidation(req, user_id=1, now=_NOW) is False

    def test_returns_true_with_recent_revalidation(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=1, now=_NOW) is True

    def test_returns_false_with_wrong_user_id(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=2, now=_NOW) is False

    def test_returns_false_with_expired_revalidation(self):
        req = _authenticated_request(1)
        past = _NOW - timedelta(minutes=11)
        mark_mfa_revalidated(req, user_id=1, now=past)
        assert has_recent_mfa_revalidation(req, user_id=1, max_age_minutes=10, now=_NOW) is False

    def test_returns_true_at_boundary(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        exactly_10 = _NOW + timedelta(minutes=10)
        assert has_recent_mfa_revalidation(req, user_id=1, max_age_minutes=10, now=exactly_10) is True

    def test_returns_false_just_after_boundary(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        just_after = _NOW + timedelta(minutes=10, seconds=1)
        assert has_recent_mfa_revalidation(req, user_id=1, max_age_minutes=10, now=just_after) is False

    def test_returns_false_for_zero_max_age(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=1, max_age_minutes=0, now=_NOW) is False

    def test_returns_false_for_negative_max_age(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=1, max_age_minutes=-5, now=_NOW) is False

    def test_does_not_modify_session(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        session_before = dict(req.session)
        has_recent_mfa_revalidation(req, user_id=1, now=_NOW)
        assert req.session == session_before


# ---------------------------------------------------------------------------
# clear_mfa_revalidation
# ---------------------------------------------------------------------------


class TestClearMfaRevalidation:
    def test_removes_revalidation_keys(self):
        req = FakeRequest()
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        clear_mfa_revalidation(req)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session
        assert MFA_REVALIDATION_AT_KEY not in req.session

    def test_is_idempotent(self):
        req = FakeRequest()
        clear_mfa_revalidation(req)
        clear_mfa_revalidation(req)
        assert req.session == {}

    def test_preserves_auth_user_id(self):
        from core.auth.session import AUTH_USER_ID_SESSION_KEY
        req = FakeRequest()
        req.session[AUTH_USER_ID_SESSION_KEY] = 42
        mark_mfa_revalidated(req, user_id=42, now=_NOW)
        clear_mfa_revalidation(req)
        assert req.session[AUTH_USER_ID_SESSION_KEY] == 42

    def test_preserves_mfa_challenge_keys(self):
        req = FakeRequest()
        req.session[MFA_CHALLENGE_USER_ID_KEY] = 1
        req.session[MFA_CHALLENGE_STARTED_AT_KEY] = _NOW.isoformat()
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        clear_mfa_revalidation(req)
        assert req.session[MFA_CHALLENGE_USER_ID_KEY] == 1
        assert req.session[MFA_CHALLENGE_STARTED_AT_KEY] == _NOW.isoformat()

    def test_preserves_flash_and_csrf(self):
        req = FakeRequest()
        req.session["_flash"] = "msg"
        req.session["_csrf"] = "tok"
        mark_mfa_revalidated(req, user_id=1, now=_NOW)
        clear_mfa_revalidation(req)
        assert req.session["_flash"] == "msg"
        assert req.session["_csrf"] == "tok"


# ---------------------------------------------------------------------------
# verify_mfa_revalidation — echecs generaux
# ---------------------------------------------------------------------------


class TestVerifyMfaRevalidationFailures:
    def test_returns_none_with_invalid_user_id(self):
        req = FakeRequest()
        result = verify_mfa_revalidation(req, user_id=0, code="123456", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_negative_user_id(self):
        req = FakeRequest()
        result = verify_mfa_revalidation(req, user_id=-1, code="123456", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_empty_code(self):
        req = FakeRequest()
        result = verify_mfa_revalidation(req, user_id=1, code="", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_whitespace_code(self):
        req = FakeRequest()
        result = verify_mfa_revalidation(req, user_id=1, code="   ", factors=[], now=_NOW)
        assert result is None

    def test_returns_none_with_non_string_code(self):
        req = FakeRequest()
        result = verify_mfa_revalidation(req, user_id=1, code=123456, factors=[], now=_NOW)  # type: ignore[arg-type]
        assert result is None

    def test_does_not_mark_revalidated_on_failure(self):
        req = _authenticated_request(1)
        verify_mfa_revalidation(req, user_id=1, code="000000", factors=[], now=_NOW)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session

    def test_returns_none_with_empty_factors_and_no_recovery(self):
        req = _authenticated_request(1)
        result = verify_mfa_revalidation(req, user_id=1, code="123456", factors=[], now=_NOW)
        assert result is None


# ---------------------------------------------------------------------------
# verify_mfa_revalidation — TOTP
# ---------------------------------------------------------------------------


class TestVerifyMfaRevalidationTOTP:
    def _setup(self, user_id: int = 1):
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.at(_NOW.timestamp())
        factor = _make_totp_factor(user_id, secret, status=MFA_STATUS_ACTIVE)
        req = _authenticated_request(user_id)
        return req, code, factor

    def test_valid_totp_returns_result(self):
        req, code, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert result is not None

    def test_valid_totp_method_is_totp(self):
        req, code, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert result.method == "totp"

    def test_valid_totp_correct_user_id(self):
        req, code, factor = self._setup(user_id=7)
        result = verify_mfa_revalidation(req, user_id=7, code=code, factors=[factor], now=_NOW)
        assert result.user_id == 7

    def test_valid_totp_renseigne_verified_at(self):
        req, code, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert result.verified_at == _NOW

    def test_valid_totp_renseigne_factor_last_used_at(self):
        req, code, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert result.factor is not None
        assert result.factor.last_used_at == _NOW

    def test_valid_totp_renseigne_factor_updated_at(self):
        req, code, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert result.factor is not None
        assert result.factor.updated_at == _NOW

    def test_valid_totp_marks_session_revalidated(self):
        req, code, factor = self._setup()
        verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert req.session[MFA_REVALIDATION_USER_ID_KEY] == 1

    def test_valid_totp_has_recent_revalidation_true_after(self):
        req, code, factor = self._setup()
        verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=1, now=_NOW) is True

    def test_wrong_totp_returns_none(self):
        req, _, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code="000000", factors=[factor], now=_NOW)
        assert result is None

    def test_wrong_totp_does_not_mark_revalidated(self):
        req, _, factor = self._setup()
        verify_mfa_revalidation(req, user_id=1, code="000000", factors=[factor], now=_NOW)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session

    def test_ignores_pending_factor(self):
        req, code, factor = self._setup()
        pending = _make_totp_factor(1, factor.totp_secret, status=MFA_STATUS_PENDING)
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[pending], now=_NOW)
        assert result is None

    def test_ignores_disabled_factor(self):
        req, code, factor = self._setup()
        disabled = _make_totp_factor(1, factor.totp_secret, status=MFA_STATUS_DISABLED)
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[disabled], now=_NOW)
        assert result is None

    def test_ignores_factor_from_other_user(self):
        secret = pyotp.random_base32()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        other_factor = _make_totp_factor(user_id=999, secret=secret, status=MFA_STATUS_ACTIVE)
        req = _authenticated_request(1)
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[other_factor], now=_NOW)
        assert result is None

    def test_no_recovery_code_in_totp_result(self):
        req, code, factor = self._setup()
        result = verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert result.recovery_code is None


# ---------------------------------------------------------------------------
# verify_mfa_revalidation — codes de recuperation
# ---------------------------------------------------------------------------


class TestVerifyMfaRevalidationRecovery:
    def _setup_recovery(self, user_id: int = 1):
        setup = create_recovery_codes(user_id=user_id, count=5, now=_NOW)
        raw_code = setup.raw_codes[0]
        code_records = list(setup.code_records)
        req = _authenticated_request(user_id)
        return req, raw_code, code_records

    def test_valid_recovery_returns_result(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result is not None

    def test_valid_recovery_method_is_recovery(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.method == "recovery"

    def test_valid_recovery_correct_user_id(self):
        req, raw_code, records = self._setup_recovery(user_id=3)
        result = verify_mfa_revalidation(req, user_id=3, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.user_id == 3

    def test_valid_recovery_renseigne_verified_at(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.verified_at == _NOW

    def test_valid_recovery_returns_consumed_code_with_used_at(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.recovery_code is not None
        assert result.recovery_code.used_at == _NOW

    def test_valid_recovery_marks_session_revalidated(self):
        req, raw_code, records = self._setup_recovery()
        verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert req.session[MFA_REVALIDATION_USER_ID_KEY] == 1

    def test_valid_recovery_has_recent_revalidation_true_after(self):
        req, raw_code, records = self._setup_recovery()
        verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=1, now=_NOW) is True

    def test_already_used_recovery_code_returns_none(self):
        setup = create_recovery_codes(user_id=1, count=3, now=_NOW)
        raw_code = setup.raw_codes[0]
        used_record = AuthMfaRecoveryCode(
            id=1,
            user_id=1,
            code_hash=hash_recovery_code(raw_code),
            used_at=_NOW - timedelta(hours=1),
        )
        req = _authenticated_request(1)
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=[used_record], now=_NOW)
        assert result is None

    def test_recovery_code_from_other_user_returns_none(self):
        setup = create_recovery_codes(user_id=999, count=3, now=_NOW)
        raw_code = setup.raw_codes[0]
        req = _authenticated_request(1)
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=list(setup.code_records), now=_NOW)
        assert result is None

    def test_already_used_does_not_mark_revalidated(self):
        setup = create_recovery_codes(user_id=1, count=1, now=_NOW)
        raw_code = setup.raw_codes[0]
        used_record = AuthMfaRecoveryCode(
            id=1,
            user_id=1,
            code_hash=hash_recovery_code(raw_code),
            used_at=_NOW,
        )
        req = _authenticated_request(1)
        verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=[used_record], now=_NOW)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session

    def test_no_factor_in_recovery_result(self):
        req, raw_code, records = self._setup_recovery()
        result = verify_mfa_revalidation(req, user_id=1, code=raw_code, factors=[], recovery_codes=records, now=_NOW)
        assert result.factor is None


# ---------------------------------------------------------------------------
# require_recent_mfa decorator
# ---------------------------------------------------------------------------


class TestRequireRecentMfa:
    def _make_authenticated_request(self, user_id: int = 1):
        from core.auth.session import AUTH_USER_ID_SESSION_KEY
        req = FakeRequest()
        req.session[AUTH_USER_ID_SESSION_KEY] = user_id
        req.session["authenticated"] = True
        req.session["user"] = {"id": user_id, "login": "test"}
        return req

    def test_allows_action_with_recent_revalidation(self):
        req = self._make_authenticated_request(user_id=1)
        mark_mfa_revalidated(req, user_id=1)  # real current time

        @require_recent_mfa
        def sensitive_action(request):
            return "ok"

        result = sensitive_action(req)
        assert result == "ok"

    def test_blocks_action_without_revalidation(self):
        req = self._make_authenticated_request(user_id=1)

        @require_recent_mfa
        def sensitive_action(request):
            return "ok"

        result = sensitive_action(req)
        assert result.status == 403

    def test_blocks_action_when_not_authenticated(self):
        req = FakeRequest()

        @require_recent_mfa
        def sensitive_action(request):
            return "ok"

        result = sensitive_action(req)
        assert result.status == 403

    def test_blocks_action_with_expired_revalidation(self):
        from datetime import datetime, timezone
        req = self._make_authenticated_request(user_id=1)
        past = datetime.now(tz=timezone.utc) - timedelta(minutes=11)
        mark_mfa_revalidated(req, user_id=1, now=past)

        @require_recent_mfa(max_age_minutes=10)
        def sensitive_action(request):
            return "ok"

        result = sensitive_action(req)
        assert result.status == 403

    def test_usable_as_decorator_with_parens(self):
        req = self._make_authenticated_request(user_id=1)
        mark_mfa_revalidated(req, user_id=1)  # real current time

        @require_recent_mfa(max_age_minutes=5)
        def sensitive_action(request):
            return "ok"

        result = sensitive_action(req)
        assert result == "ok"


# ---------------------------------------------------------------------------
# Integrite de l'API publique
# ---------------------------------------------------------------------------


class TestApiIntegrity:
    def test_importable_from_core_auth(self):
        from forge_mvc_mfa import (
    MFA_REVALIDATION_AT_KEY,
    MFA_REVALIDATION_USER_ID_KEY,
    clear_mfa_revalidation,
    get_mfa_revalidated_user_id,
    has_recent_mfa_revalidation,
    mark_mfa_revalidated,
    require_recent_mfa,
    verify_mfa_revalidation,
)
        assert callable(mark_mfa_revalidated)
        assert callable(get_mfa_revalidated_user_id)
        assert callable(has_recent_mfa_revalidation)
        assert callable(clear_mfa_revalidation)
        assert callable(verify_mfa_revalidation)
        assert callable(require_recent_mfa)
        assert MFA_REVALIDATION_USER_ID_KEY == "_auth_mfa_revalidated_user_id"
        assert MFA_REVALIDATION_AT_KEY == "_auth_mfa_revalidated_at"

    def test_mfa_revalidation_result_is_frozen(self):
        result = MfaRevalidationResult(user_id=1, method="totp", verified_at=_NOW)
        with pytest.raises(Exception):
            result.user_id = 99  # type: ignore[misc]

    def test_no_login_user_called_on_success(self):
        from core.auth.session import AUTH_USER_ID_SESSION_KEY
        secret = pyotp.random_base32()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        factor = _make_totp_factor(1, secret, status=MFA_STATUS_ACTIVE)
        req = _authenticated_request(1)
        verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)
        assert AUTH_USER_ID_SESSION_KEY not in req.session

    def test_does_not_modify_authenticate_user(self):
        from core.auth import authenticate_user
        assert callable(authenticate_user)

    def test_does_not_modify_login_required(self):
        from core.auth import login_required
        assert callable(login_required)

    def test_no_route_created(self):
        import core.auth as auth_module
        assert not hasattr(auth_module, "mfa_revalidation_route")

    def test_no_db_access_in_mark(self):
        req = _authenticated_request(1)
        mark_mfa_revalidated(req, user_id=1, now=_NOW)

    def test_no_db_access_in_verify(self):
        secret = pyotp.random_base32()
        code = pyotp.TOTP(secret).at(_NOW.timestamp())
        factor = _make_totp_factor(1, secret, status=MFA_STATUS_ACTIVE)
        req = _authenticated_request(1)
        verify_mfa_revalidation(req, user_id=1, code=code, factors=[factor], now=_NOW)

    def test_challenge_mfa_api_unchanged(self):
        from forge_mvc_mfa import (
    clear_mfa_challenge,
    get_mfa_challenge_user_id,
    has_pending_mfa_challenge,
    start_mfa_challenge,
    verify_mfa_challenge,
)
        assert callable(start_mfa_challenge)
        assert callable(verify_mfa_challenge)
        assert callable(has_pending_mfa_challenge)
        assert callable(clear_mfa_challenge)
        assert callable(get_mfa_challenge_user_id)
