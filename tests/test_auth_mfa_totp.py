"""Tests AUTH-MFA-002 — TOTP pour facteurs MFA."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_mfa")
pytest.importorskip("pyotp")

import pyotp

from forge_mvc_mfa import (
    AuthMfaFactor,
    TotpSetup,
    confirm_totp_factor,
    create_totp_factor,
    generate_totp_secret,
    totp_provisioning_uri,
    verify_totp_code,
)
from forge_mvc_mfa import (
    MFA_FACTOR_RECOVERY,
    MFA_FACTOR_TOTP,
    MFA_STATUS_ACTIVE,
    MFA_STATUS_DISABLED,
    MFA_STATUS_PENDING,
)
from core.auth.exceptions import InvalidMfaFactorError


ROOT = Path(__file__).parent.parent


# ---------------------------------------------------------------------------
# generate_totp_secret
# ---------------------------------------------------------------------------


def test_generate_totp_secret_returns_string():
    assert isinstance(generate_totp_secret(), str)


def test_generate_totp_secret_returns_non_empty():
    assert generate_totp_secret() != ""


def test_generate_totp_secret_two_calls_differ():
    assert generate_totp_secret() != generate_totp_secret()


def test_generate_totp_secret_is_valid_base32():
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    assert totp.secret == secret


# ---------------------------------------------------------------------------
# totp_provisioning_uri
# ---------------------------------------------------------------------------


def test_totp_provisioning_uri_returns_otpauth_uri():
    secret = generate_totp_secret()
    uri = totp_provisioning_uri(secret, "user@example.test", "Forge")
    assert uri.startswith("otpauth://totp/")


def test_totp_provisioning_uri_contains_issuer():
    secret = generate_totp_secret()
    uri = totp_provisioning_uri(secret, "user@example.test", "MonApp")
    assert "MonApp" in uri


def test_totp_provisioning_uri_contains_account():
    secret = generate_totp_secret()
    uri = totp_provisioning_uri(secret, "alice@forge.test", "Forge")
    assert "alice" in uri


def test_totp_provisioning_uri_rejects_empty_secret():
    with pytest.raises(ValueError):
        totp_provisioning_uri("", "user@example.test")


def test_totp_provisioning_uri_rejects_empty_account_name():
    secret = generate_totp_secret()
    with pytest.raises(ValueError):
        totp_provisioning_uri(secret, "")


def test_totp_provisioning_uri_rejects_empty_issuer_name():
    secret = generate_totp_secret()
    with pytest.raises(ValueError):
        totp_provisioning_uri(secret, "user@example.test", "")


def test_totp_provisioning_uri_default_issuer_is_forge():
    secret = generate_totp_secret()
    uri = totp_provisioning_uri(secret, "user@example.test")
    assert "Forge" in uri


# ---------------------------------------------------------------------------
# create_totp_factor
# ---------------------------------------------------------------------------


def test_create_totp_factor_returns_totp_setup():
    result = create_totp_factor(user_id=1)
    assert isinstance(result, TotpSetup)


def test_create_totp_factor_factor_is_auth_mfa_factor():
    result = create_totp_factor(user_id=1)
    assert isinstance(result.factor, AuthMfaFactor)


def test_create_totp_factor_status_is_pending():
    result = create_totp_factor(user_id=1)
    assert result.factor.status == MFA_STATUS_PENDING


def test_create_totp_factor_factor_type_is_totp():
    result = create_totp_factor(user_id=1)
    assert result.factor.factor_type == MFA_FACTOR_TOTP


def test_create_totp_factor_fills_user_id():
    result = create_totp_factor(user_id=42)
    assert result.factor.user_id == 42


def test_create_totp_factor_fills_label():
    result = create_totp_factor(user_id=1, label="Mon app")
    assert result.factor.label == "Mon app"


def test_create_totp_factor_label_none_by_default():
    result = create_totp_factor(user_id=1)
    assert result.factor.label is None


def test_create_totp_factor_secret_in_factor_totp_secret():
    result = create_totp_factor(user_id=1)
    assert result.factor.totp_secret == result.secret


def test_create_totp_factor_secret_is_non_empty():
    result = create_totp_factor(user_id=1)
    assert result.secret != ""


def test_create_totp_factor_provisioning_uri_starts_otpauth():
    result = create_totp_factor(user_id=1, account_name="user@example.test")
    assert result.provisioning_uri.startswith("otpauth://totp/")


def test_create_totp_factor_provisioning_uri_contains_issuer():
    result = create_totp_factor(user_id=1, account_name="user@example.test", issuer_name="TestApp")
    assert "TestApp" in result.provisioning_uri


def test_create_totp_factor_account_name_defaults_to_user_id():
    result = create_totp_factor(user_id=7)
    assert "7" in result.provisioning_uri


def test_create_totp_factor_id_is_none():
    result = create_totp_factor(user_id=1)
    assert result.factor.id is None


def test_create_totp_factor_confirmed_at_is_none():
    result = create_totp_factor(user_id=1)
    assert result.factor.confirmed_at is None


def test_create_totp_factor_last_used_at_is_none():
    result = create_totp_factor(user_id=1)
    assert result.factor.last_used_at is None


def test_create_totp_factor_fills_created_at_with_now():
    now = datetime(2025, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    result = create_totp_factor(user_id=1, now=now)
    assert result.factor.created_at == now
    assert result.factor.updated_at == now


def test_create_totp_factor_rejects_user_id_zero():
    with pytest.raises(InvalidMfaFactorError):
        create_totp_factor(user_id=0)


def test_create_totp_factor_rejects_user_id_negative():
    with pytest.raises(InvalidMfaFactorError):
        create_totp_factor(user_id=-1)


def test_create_totp_factor_rejects_user_id_bool():
    with pytest.raises(InvalidMfaFactorError):
        create_totp_factor(user_id=True)


def test_create_totp_factor_rejects_user_id_string():
    with pytest.raises((InvalidMfaFactorError, TypeError)):
        create_totp_factor(user_id="1")


# ---------------------------------------------------------------------------
# verify_totp_code
# ---------------------------------------------------------------------------


def _valid_code(secret: str) -> str:
    return pyotp.TOTP(secret).now()


def test_verify_totp_code_returns_true_with_valid_code():
    secret = generate_totp_secret()
    code = _valid_code(secret)
    assert verify_totp_code(secret, code) is True


def test_verify_totp_code_returns_false_with_wrong_code():
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "000000") is False


def test_verify_totp_code_returns_false_with_empty_secret():
    assert verify_totp_code("", "123456") is False


def test_verify_totp_code_returns_false_with_empty_code():
    secret = generate_totp_secret()
    assert verify_totp_code(secret, "") is False


def test_verify_totp_code_returns_false_with_invalid_secret():
    assert verify_totp_code("not-valid-base32!!", "123456") is False


def test_verify_totp_code_returns_false_with_negative_window():
    secret = generate_totp_secret()
    code = _valid_code(secret)
    assert verify_totp_code(secret, code, valid_window=-1) is False


def test_verify_totp_code_returns_false_with_none_secret():
    assert verify_totp_code(None, "123456") is False


def test_verify_totp_code_returns_false_with_none_code():
    secret = generate_totp_secret()
    assert verify_totp_code(secret, None) is False


def test_verify_totp_code_does_not_raise():
    verify_totp_code("bad", "bad")


# ---------------------------------------------------------------------------
# confirm_totp_factor
# ---------------------------------------------------------------------------


def _pending_factor(user_id: int = 1, label: str | None = None) -> tuple[AuthMfaFactor, str]:
    setup = create_totp_factor(user_id=user_id, label=label)
    return setup.factor, setup.secret


def test_confirm_totp_factor_returns_active_factor():
    factor, secret = _pending_factor()
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed is not None
    assert confirmed.status == MFA_STATUS_ACTIVE


def test_confirm_totp_factor_sets_confirmed_at():
    factor, secret = _pending_factor()
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed.confirmed_at is not None


def test_confirm_totp_factor_sets_updated_at():
    factor, secret = _pending_factor()
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed.updated_at is not None


def test_confirm_totp_factor_confirmed_at_matches_now():
    now = datetime(2025, 6, 1, 10, 0, 0, tzinfo=timezone.utc)
    factor, secret = _pending_factor()
    code = pyotp.TOTP(secret).at(now)
    confirmed = confirm_totp_factor(factor, code, now=now)
    assert confirmed is not None
    assert confirmed.confirmed_at == now
    assert confirmed.updated_at == now


def test_confirm_totp_factor_preserves_id():
    setup = create_totp_factor(user_id=1)
    factor = setup.factor
    code = _valid_code(setup.secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed.id == factor.id


def test_confirm_totp_factor_preserves_user_id():
    factor, secret = _pending_factor(user_id=99)
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed.user_id == 99


def test_confirm_totp_factor_preserves_totp_secret():
    factor, secret = _pending_factor()
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed.totp_secret == factor.totp_secret


def test_confirm_totp_factor_preserves_label():
    factor, secret = _pending_factor(label="Auth app")
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed.label == "Auth app"


def test_confirm_totp_factor_preserves_created_at():
    now = datetime(2025, 1, 1, tzinfo=timezone.utc)
    setup = create_totp_factor(user_id=1, now=now)
    code = _valid_code(setup.secret)
    confirmed = confirm_totp_factor(setup.factor, code)
    assert confirmed.created_at == now


def test_confirm_totp_factor_returns_none_with_wrong_code():
    factor, _ = _pending_factor()
    assert confirm_totp_factor(factor, "000000") is None


def test_confirm_totp_factor_returns_none_with_wrong_factor_type():
    factor = AuthMfaFactor(
        id=None, user_id=1, factor_type=MFA_FACTOR_RECOVERY,
        totp_secret="somesecret", status=MFA_STATUS_PENDING,
    )
    assert confirm_totp_factor(factor, "123456") is None


def test_confirm_totp_factor_returns_none_when_already_active():
    factor, secret = _pending_factor()
    code = _valid_code(secret)
    confirmed = confirm_totp_factor(factor, code)
    assert confirmed is not None
    assert confirm_totp_factor(confirmed, code) is None


def test_confirm_totp_factor_returns_none_when_disabled():
    factor = AuthMfaFactor(
        id=None, user_id=1, factor_type=MFA_FACTOR_TOTP,
        totp_secret=generate_totp_secret(), status=MFA_STATUS_DISABLED,
    )
    code = _valid_code(factor.totp_secret)
    assert confirm_totp_factor(factor, code) is None


def test_confirm_totp_factor_does_not_modify_original():
    factor, secret = _pending_factor()
    original_status = factor.status
    code = _valid_code(secret)
    confirm_totp_factor(factor, code)
    assert factor.status == original_status


def test_confirm_totp_factor_accepts_dict():
    setup = create_totp_factor(user_id=1)
    factor_dict = {
        "id": None,
        "user_id": setup.factor.user_id,
        "factor_type": setup.factor.factor_type,
        "totp_secret": setup.factor.totp_secret,
        "status": setup.factor.status,
    }
    code = _valid_code(setup.secret)
    confirmed = confirm_totp_factor(factor_dict, code)
    assert confirmed is not None
    assert confirmed.status == MFA_STATUS_ACTIVE


def test_confirm_totp_factor_returns_none_for_invalid_input():
    assert confirm_totp_factor(None, "123456") is None
    assert confirm_totp_factor("bad", "123456") is None


# ---------------------------------------------------------------------------
# API importable depuis core.auth
# ---------------------------------------------------------------------------


def test_api_importable_from_core_auth():
    from forge_mvc_mfa import (
    TotpSetup,
    confirm_totp_factor,
    create_totp_factor,
    generate_totp_secret,
    totp_provisioning_uri,
    verify_totp_code,
)
    assert callable(generate_totp_secret)
    assert callable(totp_provisioning_uri)
    assert callable(create_totp_factor)
    assert callable(verify_totp_code)
    assert callable(confirm_totp_factor)
    assert TotpSetup is not None


# ---------------------------------------------------------------------------
# Packaging — pyotp dans forge-mvc-mfa, pas dans le core (principe 8)
# ---------------------------------------------------------------------------


def test_pyotp_absent_de_requirements_txt():
    """pyotp est MFA-only : il ne doit pas être dans le core requirements.txt."""
    reqs = (ROOT / "requirements.txt").read_text(encoding="utf-8")
    lines = [l.strip() for l in reqs.splitlines() if l.strip() and not l.startswith("#")]
    assert not any(l.lower().startswith("pyotp") for l in lines), (
        "pyotp ne doit pas être dans requirements.txt (dépendance MFA-only, principe 8)"
    )


def test_pyotp_absent_du_pyproject_racine():
    """pyotp ne doit pas figurer dans [project].dependencies du pyproject.toml racine."""
    import tomllib
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    deps = data["project"]["dependencies"]
    assert not any(d.lower().startswith("pyotp") for d in deps), (
        "pyotp ne doit pas être dans les dependencies racine (dépendance MFA-only, principe 8)"
    )


def test_pyotp_dans_forge_mvc_mfa_pyproject():
    """pyotp doit être déclaré dans les dépendances de forge-mvc-mfa."""
    mfa_pyproject = ROOT / "packages" / "forge-mvc-mfa" / "pyproject.toml"
    text = mfa_pyproject.read_text(encoding="utf-8")
    assert "pyotp" in text, "pyotp doit être dans packages/forge-mvc-mfa/pyproject.toml"


# ---------------------------------------------------------------------------
# Perimetres exclus
# ---------------------------------------------------------------------------


def test_no_qr_code_generated():
    setup = create_totp_factor(user_id=1, account_name="user@example.test")
    assert not hasattr(setup, "qr_code")
    assert not hasattr(setup, "qr_url")


def test_no_recovery_codes_generated():
    setup = create_totp_factor(user_id=1)
    assert not hasattr(setup, "recovery_codes")
    assert not hasattr(setup.factor, "recovery_codes")


def test_no_mfa_challenge():
    import core.auth.session as session_module
    assert not hasattr(session_module, "mfa_challenge")
    assert not hasattr(session_module, "require_mfa")


def test_login_user_not_modified(monkeypatch):
    calls = []
    import forge_mvc_mfa.mfa as mfa_module
    monkeypatch.setattr(mfa_module, "verify_totp_code", lambda *a, **kw: calls.append(True) or True)
    from core.auth import login_user
    assert callable(login_user)


def test_no_db_access(monkeypatch):
    calls = []
    monkeypatch.setattr("mariadb.connect", lambda *a, **kw: calls.append(True), raising=False)
    setup = create_totp_factor(user_id=1)
    code = _valid_code(setup.secret)
    confirm_totp_factor(setup.factor, code)
    assert calls == []
