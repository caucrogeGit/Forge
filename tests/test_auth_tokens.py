"""Tests AUTH-TOKEN-001 — jetons auth generiques Forge."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.auth import (
    AuthToken,
    generate_auth_token,
    hash_auth_token,
    is_token_expired,
    is_token_usable,
    is_valid_auth_token,
    normalize_auth_token,
    token_expires_at,
    validate_auth_token_contract,
    verify_auth_token,
)
from core.auth.tokens import InvalidAuthTokenError


# ---------------------------------------------------------------------------
# generate_auth_token
# ---------------------------------------------------------------------------


def test_generate_auth_token_returns_string():
    token = generate_auth_token()
    assert isinstance(token, str)


def test_generate_auth_token_two_tokens_are_different():
    assert generate_auth_token() != generate_auth_token()


def test_generate_auth_token_refuses_zero():
    with pytest.raises(ValueError):
        generate_auth_token(0)


def test_generate_auth_token_refuses_negative():
    with pytest.raises(ValueError):
        generate_auth_token(-1)


def test_generate_auth_token_no_spaces():
    token = generate_auth_token()
    assert " " not in token


def test_generate_auth_token_custom_nbytes():
    token = generate_auth_token(16)
    assert isinstance(token, str)
    assert len(token) > 0


# ---------------------------------------------------------------------------
# hash_auth_token
# ---------------------------------------------------------------------------


def test_hash_auth_token_returns_string():
    h = hash_auth_token("mytoken")
    assert isinstance(h, str)


def test_hash_auth_token_does_not_return_token():
    token = "mytoken"
    h = hash_auth_token(token)
    assert h != token


def test_hash_auth_token_is_deterministic():
    token = "mytoken"
    assert hash_auth_token(token) == hash_auth_token(token)


def test_hash_auth_token_returns_64_hex_chars():
    h = hash_auth_token("mytoken")
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


# ---------------------------------------------------------------------------
# verify_auth_token
# ---------------------------------------------------------------------------


def test_verify_auth_token_returns_true_with_correct_token():
    token = generate_auth_token()
    h = hash_auth_token(token)
    assert verify_auth_token(token, h) is True


def test_verify_auth_token_returns_false_with_wrong_token():
    token = generate_auth_token()
    h = hash_auth_token(token)
    assert verify_auth_token("wrong-token", h) is False


def test_verify_auth_token_returns_false_with_empty_token():
    h = hash_auth_token("mytoken")
    assert verify_auth_token("", h) is False


def test_verify_auth_token_returns_false_with_empty_hash():
    token = generate_auth_token()
    assert verify_auth_token(token, "") is False


def test_verify_auth_token_returns_false_with_invalid_hash():
    token = generate_auth_token()
    assert verify_auth_token(token, "not-a-valid-hash") is False


def test_verify_auth_token_returns_false_both_empty():
    assert verify_auth_token("", "") is False


# ---------------------------------------------------------------------------
# token_expires_at
# ---------------------------------------------------------------------------


def test_token_expires_at_returns_future_datetime():
    now = datetime.now(tz=timezone.utc)
    exp = token_expires_at(60, now=now)
    assert exp > now


def test_token_expires_at_default_is_60_minutes():
    now = datetime.now(tz=timezone.utc)
    exp = token_expires_at(now=now)
    assert exp == now + timedelta(minutes=60)


def test_token_expires_at_custom_minutes():
    now = datetime.now(tz=timezone.utc)
    exp = token_expires_at(30, now=now)
    assert exp == now + timedelta(minutes=30)


# ---------------------------------------------------------------------------
# is_token_expired
# ---------------------------------------------------------------------------


def test_is_token_expired_false_before_expiration():
    now = datetime.now(tz=timezone.utc)
    exp = now + timedelta(minutes=10)
    assert is_token_expired(exp, now=now) is False


def test_is_token_expired_true_after_expiration():
    now = datetime.now(tz=timezone.utc)
    exp = now - timedelta(seconds=1)
    assert is_token_expired(exp, now=now) is True


def test_is_token_expired_true_at_exact_expiration():
    now = datetime.now(tz=timezone.utc)
    assert is_token_expired(now, now=now) is True


# ---------------------------------------------------------------------------
# is_token_usable
# ---------------------------------------------------------------------------

def _make_token(*, expired=False, used=False, purpose="reset"):
    now = datetime.now(tz=timezone.utc)
    expires_at = now - timedelta(minutes=1) if expired else now + timedelta(minutes=60)
    used_at = now if used else None
    return AuthToken(
        user_id=1,
        purpose=purpose,
        token_hash="abc" * 21 + "a",
        expires_at=expires_at,
        used_at=used_at,
    )


def test_is_token_usable_true_valid_token():
    token = _make_token()
    assert is_token_usable(token, purpose="reset") is True


def test_is_token_usable_true_no_purpose_check():
    token = _make_token()
    assert is_token_usable(token) is True


def test_is_token_usable_false_if_expired():
    token = _make_token(expired=True)
    assert is_token_usable(token) is False


def test_is_token_usable_false_if_used():
    token = _make_token(used=True)
    assert is_token_usable(token) is False


def test_is_token_usable_false_if_wrong_purpose():
    token = _make_token(purpose="reset")
    assert is_token_usable(token, purpose="verify-email") is False


def test_is_token_usable_accepts_dict():
    now = datetime.now(tz=timezone.utc)
    data = {
        "user_id": 1,
        "purpose": "reset",
        "token_hash": "a" * 64,
        "expires_at": now + timedelta(minutes=30),
        "used_at": None,
    }
    assert is_token_usable(data, purpose="reset") is True


def test_is_token_usable_false_with_invalid_data():
    assert is_token_usable(None) is False
    assert is_token_usable({}) is False
    assert is_token_usable("not-a-token") is False


# ---------------------------------------------------------------------------
# AuthToken et normalisation
# ---------------------------------------------------------------------------


def test_auth_token_is_a_dataclass():
    now = datetime.now(tz=timezone.utc)
    token = AuthToken(
        user_id=1,
        purpose="reset",
        token_hash="a" * 64,
        expires_at=now + timedelta(minutes=60),
    )
    assert token.user_id == 1
    assert token.purpose == "reset"
    assert token.used_at is None
    assert token.created_at is None


def test_normalize_auth_token_from_dict():
    now = datetime.now(tz=timezone.utc)
    data = {
        "user_id": 2,
        "purpose": " verify-email ",
        "token_hash": "b" * 64,
        "expires_at": now + timedelta(hours=1),
    }
    token = normalize_auth_token(data)
    assert isinstance(token, AuthToken)
    assert token.purpose == "verify-email"
    assert token.user_id == 2


def test_validate_auth_token_contract_accepts_auth_token():
    now = datetime.now(tz=timezone.utc)
    token = AuthToken(
        user_id=1,
        purpose="reset",
        token_hash="c" * 64,
        expires_at=now + timedelta(minutes=10),
    )
    assert validate_auth_token_contract(token) is None


def test_validate_auth_token_contract_rejects_missing_fields():
    with pytest.raises(InvalidAuthTokenError):
        validate_auth_token_contract({"user_id": 1})


def test_is_valid_auth_token_true_for_valid():
    now = datetime.now(tz=timezone.utc)
    token = AuthToken(
        user_id=1,
        purpose="reset",
        token_hash="d" * 64,
        expires_at=now + timedelta(minutes=10),
    )
    assert is_valid_auth_token(token) is True


def test_is_valid_auth_token_false_for_dict():
    now = datetime.now(tz=timezone.utc)
    data = {
        "user_id": 1,
        "purpose": "reset",
        "token_hash": "e" * 64,
        "expires_at": now + timedelta(minutes=10),
    }
    assert is_valid_auth_token(data) is False


# ---------------------------------------------------------------------------
# Perimetres exclus — aucun acces base, session, route, mail, MFA, RBAC
# ---------------------------------------------------------------------------


def test_no_database_access_in_token_generation(monkeypatch):
    calls = []

    def fake_connect(*a, **kw):
        calls.append(True)
        raise RuntimeError("connexion base non autorisee")

    monkeypatch.setattr("mariadb.connect", fake_connect, raising=False)
    token = generate_auth_token()
    assert isinstance(token, str)
    assert calls == []


def test_no_session_created_in_token_generation(monkeypatch):
    calls = []
    import core.security.session as session_module

    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")
    generate_auth_token()
    assert calls == []


def test_api_importable_from_core_auth():
    from core.auth import (
        AuthToken,
        generate_auth_token,
        hash_auth_token,
        is_token_expired,
        is_token_usable,
        token_expires_at,
        verify_auth_token,
    )

    assert callable(generate_auth_token)
    assert callable(hash_auth_token)
    assert callable(verify_auth_token)
    assert callable(token_expires_at)
    assert callable(is_token_expired)
    assert callable(is_token_usable)
    assert AuthToken is not None
