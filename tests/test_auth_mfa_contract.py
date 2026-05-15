"""Tests AUTH-MFA-001 — contrat MFA generique."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest
pytest.importorskip("forge_mvc_mfa")

from forge_mvc_mfa import (
    MFA_FACTOR_RECOVERY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    MFA_STATUS_DISABLED,
    MFA_STATUS_PENDING,
    AuthMfaFactor,
    is_mfa_enabled,
    is_mfa_factor_active,
    is_valid_mfa_factor,
    normalize_mfa_factor,
    validate_mfa_factor_contract,
)
from core.auth.exceptions import InvalidMfaFactorError


# ---------------------------------------------------------------------------
# Constantes
# ---------------------------------------------------------------------------


def test_mfa_factor_totp_value():
    assert MFA_FACTOR_TOTP == "totp"


def test_mfa_factor_recovery_value():
    assert MFA_FACTOR_RECOVERY == "recovery"


def test_mfa_status_pending_value():
    assert MFA_STATUS_PENDING == "pending"


def test_mfa_status_active_value():
    assert MFA_STATUS_ACTIVE == "active"


def test_mfa_status_disabled_value():
    assert MFA_STATUS_DISABLED == "disabled"


# ---------------------------------------------------------------------------
# AuthMfaFactor — creation directe
# ---------------------------------------------------------------------------


def test_auth_mfa_factor_creation_minimal():
    factor = AuthMfaFactor(
        id=None,
        user_id=1,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret="hash_secret",
        status=MFA_STATUS_PENDING,
    )
    assert factor.user_id == 1
    assert factor.factor_type == MFA_FACTOR_TOTP
    assert factor.totp_secret == "hash_secret"
    assert factor.status == MFA_STATUS_PENDING
    assert factor.id is None
    assert factor.label is None
    assert factor.confirmed_at is None
    assert factor.last_used_at is None


def test_auth_mfa_factor_creation_with_id():
    factor = AuthMfaFactor(
        id=42,
        user_id=1,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret="hash",
        status=MFA_STATUS_ACTIVE,
    )
    assert factor.id == 42
    assert factor.status == MFA_STATUS_ACTIVE


def test_auth_mfa_factor_creation_with_all_fields():
    now = datetime.now(tz=timezone.utc)
    factor = AuthMfaFactor(
        id=1,
        user_id=2,
        factor_type=MFA_FACTOR_TOTP,
        totp_secret="hash",
        status=MFA_STATUS_ACTIVE,
        label="Mon authenticator",
        confirmed_at=now,
        last_used_at=now,
        created_at=now,
        updated_at=now,
    )
    assert factor.label == "Mon authenticator"
    assert factor.confirmed_at == now


# ---------------------------------------------------------------------------
# validate_mfa_factor_contract
# ---------------------------------------------------------------------------


def _valid_dict(**overrides):
    base = {
        "id": None,
        "user_id": 1,
        "factor_type": MFA_FACTOR_TOTP,
        "totp_secret": "hash_secret",
        "status": MFA_STATUS_PENDING,
    }
    base.update(overrides)
    return base


def test_validate_accepts_auth_mfa_factor():
    factor = AuthMfaFactor(id=None, user_id=1, factor_type=MFA_FACTOR_TOTP, totp_secret="h", status=MFA_STATUS_PENDING)
    assert validate_mfa_factor_contract(factor) is None


def test_validate_accepts_valid_dict():
    assert validate_mfa_factor_contract(_valid_dict()) is None


def test_validate_accepts_recovery_factor_type():
    assert validate_mfa_factor_contract(_valid_dict(factor_type=MFA_FACTOR_RECOVERY)) is None


def test_validate_accepts_all_statuses():
    for status in (MFA_STATUS_PENDING, MFA_STATUS_ACTIVE, MFA_STATUS_DISABLED):
        assert validate_mfa_factor_contract(_valid_dict(status=status)) is None


def test_validate_accepts_id_none():
    assert validate_mfa_factor_contract(_valid_dict(id=None)) is None


def test_validate_accepts_id_positive_int():
    assert validate_mfa_factor_contract(_valid_dict(id=5)) is None


def test_validate_rejects_invalid_id_zero():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(id=0))


def test_validate_rejects_invalid_id_negative():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(id=-1))


def test_validate_rejects_invalid_id_bool():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(id=True))


def test_validate_rejects_missing_user_id():
    data = {k: v for k, v in _valid_dict().items() if k != "user_id"}
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(data)


def test_validate_rejects_user_id_zero():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(user_id=0))


def test_validate_rejects_user_id_negative():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(user_id=-1))


def test_validate_rejects_missing_factor_type():
    data = {k: v for k, v in _valid_dict().items() if k != "factor_type"}
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(data)


def test_validate_rejects_unknown_factor_type():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(factor_type="sms"))


def test_validate_rejects_missing_totp_secret():
    data = {k: v for k, v in _valid_dict().items() if k != "totp_secret"}
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(data)


def test_validate_rejects_empty_totp_secret():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(totp_secret=""))


def test_validate_rejects_missing_status():
    data = {k: v for k, v in _valid_dict().items() if k != "status"}
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(data)


def test_validate_rejects_unknown_status():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(_valid_dict(status="suspended"))


def test_validate_rejects_non_dict_non_factor():
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract("not-a-factor")
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(None)
    with pytest.raises(InvalidMfaFactorError):
        validate_mfa_factor_contract(42)


# ---------------------------------------------------------------------------
# normalize_mfa_factor
# ---------------------------------------------------------------------------


def test_normalize_from_dict():
    factor = normalize_mfa_factor(_valid_dict())
    assert isinstance(factor, AuthMfaFactor)
    assert factor.user_id == 1
    assert factor.factor_type == MFA_FACTOR_TOTP


def test_normalize_from_auth_mfa_factor():
    original = AuthMfaFactor(id=None, user_id=1, factor_type=MFA_FACTOR_TOTP, totp_secret="h", status=MFA_STATUS_PENDING)
    result = normalize_mfa_factor(original)
    assert result is original


def test_normalize_preserves_optional_fields():
    now = datetime.now(tz=timezone.utc)
    data = _valid_dict(label="Auth app", confirmed_at=now, last_used_at=now)
    factor = normalize_mfa_factor(data)
    assert factor.label == "Auth app"
    assert factor.confirmed_at == now


def test_normalize_raises_on_invalid_data():
    with pytest.raises(InvalidMfaFactorError):
        normalize_mfa_factor({"user_id": 1})


# ---------------------------------------------------------------------------
# is_valid_mfa_factor
# ---------------------------------------------------------------------------


def test_is_valid_returns_true_for_valid_factor():
    factor = AuthMfaFactor(id=None, user_id=1, factor_type=MFA_FACTOR_TOTP, totp_secret="h", status=MFA_STATUS_PENDING)
    assert is_valid_mfa_factor(factor) is True


def test_is_valid_returns_false_for_dict():
    assert is_valid_mfa_factor(_valid_dict()) is False


def test_is_valid_returns_false_for_none():
    assert is_valid_mfa_factor(None) is False


def test_is_valid_returns_false_for_invalid_factor():
    bad_factor = AuthMfaFactor(id=None, user_id=0, factor_type=MFA_FACTOR_TOTP, totp_secret="h", status=MFA_STATUS_PENDING)
    assert is_valid_mfa_factor(bad_factor) is False


# ---------------------------------------------------------------------------
# is_mfa_factor_active
# ---------------------------------------------------------------------------


def _make_factor(status: str) -> AuthMfaFactor:
    return AuthMfaFactor(id=None, user_id=1, factor_type=MFA_FACTOR_TOTP, totp_secret="h", status=status)


def test_is_active_returns_true_for_active():
    assert is_mfa_factor_active(_make_factor(MFA_STATUS_ACTIVE)) is True


def test_is_active_returns_false_for_pending():
    assert is_mfa_factor_active(_make_factor(MFA_STATUS_PENDING)) is False


def test_is_active_returns_false_for_disabled():
    assert is_mfa_factor_active(_make_factor(MFA_STATUS_DISABLED)) is False


def test_is_active_works_with_dict():
    assert is_mfa_factor_active({"status": MFA_STATUS_ACTIVE}) is True
    assert is_mfa_factor_active({"status": MFA_STATUS_PENDING}) is False


def test_is_active_returns_false_for_invalid_input():
    assert is_mfa_factor_active(None) is False
    assert is_mfa_factor_active("active") is False


# ---------------------------------------------------------------------------
# is_mfa_enabled
# ---------------------------------------------------------------------------


def test_is_mfa_enabled_true_with_one_active_factor():
    factors = [_make_factor(MFA_STATUS_ACTIVE)]
    assert is_mfa_enabled(factors) is True


def test_is_mfa_enabled_true_with_mixed_factors():
    factors = [
        _make_factor(MFA_STATUS_PENDING),
        _make_factor(MFA_STATUS_ACTIVE),
        _make_factor(MFA_STATUS_DISABLED),
    ]
    assert is_mfa_enabled(factors) is True


def test_is_mfa_enabled_false_with_no_active_factor():
    factors = [_make_factor(MFA_STATUS_PENDING), _make_factor(MFA_STATUS_DISABLED)]
    assert is_mfa_enabled(factors) is False


def test_is_mfa_enabled_false_with_empty_list():
    assert is_mfa_enabled([]) is False


def test_is_mfa_enabled_ignores_invalid_elements():
    factors = [None, "bad", 42, _make_factor(MFA_STATUS_ACTIVE)]
    assert is_mfa_enabled(factors) is True


def test_is_mfa_enabled_false_with_only_invalid_elements():
    assert is_mfa_enabled([None, "bad", {}]) is False


def test_is_mfa_enabled_no_db_access(monkeypatch):
    calls = []
    monkeypatch.setattr("mariadb.connect", lambda *a, **kw: calls.append(True), raising=False)
    is_mfa_enabled([_make_factor(MFA_STATUS_ACTIVE)])
    assert calls == []


# ---------------------------------------------------------------------------
# Imports publics depuis core.auth
# ---------------------------------------------------------------------------


def test_api_importable_from_forge_mvc_mfa():
    from forge_mvc_mfa import (
        MFA_FACTOR_RECOVERY,
        MFA_FACTOR_TOTP,
        AuthMfaFactor,
        is_mfa_enabled,
        is_mfa_factor_active,
        is_valid_mfa_factor,
        normalize_mfa_factor,
        validate_mfa_factor_contract,
    )
    from core.auth.exceptions import InvalidMfaFactorError
    assert MFA_FACTOR_TOTP == "totp"
    assert MFA_FACTOR_RECOVERY == "recovery"
    assert AuthMfaFactor is not None
    assert issubclass(InvalidMfaFactorError, ValueError)
    assert callable(normalize_mfa_factor)
    assert callable(validate_mfa_factor_contract)
    assert callable(is_valid_mfa_factor)
    assert callable(is_mfa_factor_active)
    assert callable(is_mfa_enabled)


# ---------------------------------------------------------------------------
# Perimetres exclus
# ---------------------------------------------------------------------------


def test_no_totp_secret_auto_generated():
    factor = AuthMfaFactor(
        id=None, user_id=1, factor_type=MFA_FACTOR_TOTP,
        totp_secret="any_secret", status=MFA_STATUS_PENDING,
    )
    assert factor.totp_secret == "any_secret"  # stored as-is, not auto-regenerated
    assert not hasattr(factor, "qr_code")


def test_no_session_created(monkeypatch):
    calls = []
    import core.security.session as session_module
    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")
    normalize_mfa_factor(_valid_dict())
    assert calls == []
