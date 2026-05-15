"""Tests AUTH-RESET-001 — demande de reinitialisation de mot de passe."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.auth import (
    PASSWORD_RESET_PURPOSE,
    PasswordResetRequest,
    create_password_reset_request,
    create_password_reset_token,
    password_reset_timestamp,
    verify_password_reset_token,
)
from core.auth.exceptions import AuthError
from core.auth.tokens import AuthToken, hash_auth_token
from core.auth.user import AuthUser


# ---------------------------------------------------------------------------
# Constante PURPOSE
# ---------------------------------------------------------------------------


def test_password_reset_purpose_value():
    assert PASSWORD_RESET_PURPOSE == "password_reset"


def test_password_reset_purpose_differs_from_email_verification():
    from core.auth import EMAIL_VERIFICATION_PURPOSE
    assert PASSWORD_RESET_PURPOSE != EMAIL_VERIFICATION_PURPOSE


# ---------------------------------------------------------------------------
# create_password_reset_token
# ---------------------------------------------------------------------------


def test_create_returns_tuple_str_and_auth_token():
    raw_token, auth_token = create_password_reset_token(user_id=1)
    assert isinstance(raw_token, str)
    assert isinstance(auth_token, AuthToken)


def test_create_token_brut_differs_from_hash():
    raw_token, auth_token = create_password_reset_token(user_id=1)
    assert raw_token != auth_token.token_hash


def test_create_auth_token_user_id():
    _, auth_token = create_password_reset_token(user_id=7)
    assert auth_token.user_id == 7


def test_create_auth_token_purpose():
    _, auth_token = create_password_reset_token(user_id=1)
    assert auth_token.purpose == PASSWORD_RESET_PURPOSE


def test_create_auth_token_expires_at_is_future():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_password_reset_token(user_id=1, now=now)
    assert auth_token.expires_at > now


def test_create_auth_token_default_expires_in_30_minutes():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_password_reset_token(user_id=1, now=now)
    assert auth_token.expires_at == now + timedelta(minutes=30)


def test_create_auth_token_used_at_is_none():
    _, auth_token = create_password_reset_token(user_id=1)
    assert auth_token.used_at is None


def test_create_auth_token_created_at_is_set():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_password_reset_token(user_id=1, now=now)
    assert auth_token.created_at == now


def test_create_custom_minutes():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_password_reset_token(user_id=1, minutes=15, now=now)
    assert auth_token.expires_at == now + timedelta(minutes=15)


def test_create_two_tokens_differ():
    raw1, _ = create_password_reset_token(user_id=1)
    raw2, _ = create_password_reset_token(user_id=1)
    assert raw1 != raw2


def test_create_refuses_user_id_zero():
    with pytest.raises(AuthError):
        create_password_reset_token(user_id=0)


def test_create_refuses_user_id_negative():
    with pytest.raises(AuthError):
        create_password_reset_token(user_id=-5)


def test_create_refuses_user_id_string():
    with pytest.raises(AuthError):
        create_password_reset_token(user_id="abc")  # type: ignore[arg-type]


def test_create_refuses_user_id_bool():
    with pytest.raises(AuthError):
        create_password_reset_token(user_id=True)


def test_create_refuses_minutes_zero():
    with pytest.raises(AuthError):
        create_password_reset_token(user_id=1, minutes=0)


def test_create_refuses_minutes_negative():
    with pytest.raises(AuthError):
        create_password_reset_token(user_id=1, minutes=-10)


# ---------------------------------------------------------------------------
# verify_password_reset_token
# ---------------------------------------------------------------------------


def _make_reset_token(*, minutes_offset: int = 30, used: bool = False, purpose: str = PASSWORD_RESET_PURPOSE):
    now = datetime.now(tz=timezone.utc)
    raw_token, _ = create_password_reset_token(user_id=1, now=now)
    token_hash = hash_auth_token(raw_token)
    expires_at = now + timedelta(minutes=minutes_offset)
    used_at = now if used else None
    token_record = AuthToken(
        user_id=1,
        purpose=purpose,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=used_at,
    )
    return raw_token, token_record


def test_verify_returns_true_with_valid_token():
    raw_token, token_record = _make_reset_token()
    assert verify_password_reset_token(raw_token, token_record) is True


def test_verify_accepts_dict():
    raw_token, token_record = _make_reset_token()
    data = {
        "user_id": token_record.user_id,
        "purpose": token_record.purpose,
        "token_hash": token_record.token_hash,
        "expires_at": token_record.expires_at,
        "used_at": token_record.used_at,
    }
    assert verify_password_reset_token(raw_token, data) is True


def test_verify_returns_false_with_wrong_token():
    _, token_record = _make_reset_token()
    assert verify_password_reset_token("mauvais-token", token_record) is False


def test_verify_returns_false_with_empty_token():
    _, token_record = _make_reset_token()
    assert verify_password_reset_token("", token_record) is False


def test_verify_returns_false_if_expired():
    raw_token, token_record = _make_reset_token(minutes_offset=-1)
    assert verify_password_reset_token(raw_token, token_record) is False


def test_verify_returns_false_if_used():
    raw_token, token_record = _make_reset_token(used=True)
    assert verify_password_reset_token(raw_token, token_record) is False


def test_verify_returns_false_if_wrong_purpose():
    raw_token, token_record = _make_reset_token(purpose="email_verification")
    assert verify_password_reset_token(raw_token, token_record) is False


def test_verify_returns_false_with_invalid_record():
    raw_token, _ = _make_reset_token()
    assert verify_password_reset_token(raw_token, None) is False
    assert verify_password_reset_token(raw_token, {}) is False
    assert verify_password_reset_token(raw_token, 42) is False


def test_verify_does_not_modify_token_record():
    raw_token, token_record = _make_reset_token()
    verify_password_reset_token(raw_token, token_record)
    assert token_record.used_at is None


def test_verify_does_not_modify_password_hash():
    raw_token, token_record = _make_reset_token()
    original_hash = token_record.token_hash
    verify_password_reset_token(raw_token, token_record)
    assert token_record.token_hash == original_hash


# ---------------------------------------------------------------------------
# password_reset_timestamp
# ---------------------------------------------------------------------------


def test_password_reset_timestamp_returns_datetime():
    ts = password_reset_timestamp()
    assert isinstance(ts, datetime)


def test_password_reset_timestamp_accepts_now():
    now = datetime.now(tz=timezone.utc)
    assert password_reset_timestamp(now=now) == now


def test_password_reset_timestamp_default_is_utc():
    ts = password_reset_timestamp()
    assert ts.tzinfo is not None


# ---------------------------------------------------------------------------
# PasswordResetRequest
# ---------------------------------------------------------------------------


def test_password_reset_request_is_a_dataclass():
    now = datetime.now(tz=timezone.utc)
    raw_token, token_record = create_password_reset_token(user_id=1, now=now)
    req = PasswordResetRequest(
        user_id=1,
        email="alice@example.com",
        raw_token=raw_token,
        token_record=token_record,
    )
    assert req.user_id == 1
    assert req.email == "alice@example.com"
    assert req.raw_token == raw_token
    assert req.token_record is token_record


# ---------------------------------------------------------------------------
# create_password_reset_request
# ---------------------------------------------------------------------------


def _make_user(*, is_active: bool = True) -> AuthUser:
    return AuthUser(id=2, email="bob@example.com", password_hash="hash", is_active=is_active)


def test_create_request_from_auth_user():
    user = _make_user()
    req = create_password_reset_request(user)
    assert isinstance(req, PasswordResetRequest)
    assert req.user_id == user.id
    assert req.email == user.email
    assert isinstance(req.raw_token, str)
    assert isinstance(req.token_record, AuthToken)


def test_create_request_from_dict():
    data = {"id": 3, "email": "carol@example.com", "password_hash": "hash"}
    req = create_password_reset_request(data)
    assert req.user_id == 3
    assert req.email == "carol@example.com"


def test_create_request_token_has_reset_purpose():
    req = create_password_reset_request(_make_user())
    assert req.token_record.purpose == PASSWORD_RESET_PURPOSE


def test_create_request_token_brut_differs_from_hash():
    req = create_password_reset_request(_make_user())
    assert req.raw_token != req.token_record.token_hash


def test_create_request_does_not_expose_password_hash():
    user = _make_user()
    req = create_password_reset_request(user)
    assert not hasattr(req, "password_hash")


def test_create_request_refuses_inactive_user():
    user = _make_user(is_active=False)
    with pytest.raises(AuthError):
        create_password_reset_request(user)


def test_create_request_refuses_invalid_data():
    with pytest.raises(Exception):
        create_password_reset_request(None)

    with pytest.raises(Exception):
        create_password_reset_request({"id": -1, "email": "x@y.com", "password_hash": "h"})


def test_create_request_does_not_modify_user():
    user = _make_user()
    original_hash = user.password_hash
    create_password_reset_request(user)
    assert user.password_hash == original_hash


# ---------------------------------------------------------------------------
# Perimetres exclus
# ---------------------------------------------------------------------------


def test_no_password_hash_changed():
    user = _make_user()
    req = create_password_reset_request(user)
    # Verifier qu'aucun hash_password n'a ete appele pour changer le mot de passe
    assert user.password_hash == "hash"
    assert "hash" not in req.raw_token


def test_no_mail_sent(monkeypatch):
    sent = []
    monkeypatch.setattr("smtplib.SMTP", lambda *a, **kw: sent.append(True), raising=False)
    create_password_reset_token(user_id=1)
    assert sent == []


def test_no_session_created(monkeypatch):
    calls = []
    import core.security.session as session_module
    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")
    create_password_reset_token(user_id=1)
    assert calls == []


def test_no_database_access(monkeypatch):
    calls = []
    monkeypatch.setattr("mariadb.connect", lambda *a, **kw: calls.append(True), raising=False)
    create_password_reset_token(user_id=1)
    assert calls == []


def test_api_importable_from_core_auth():
    from core.auth import (
        PASSWORD_RESET_PURPOSE,
        PasswordResetRequest,
        create_password_reset_request,
        create_password_reset_token,
        password_reset_timestamp,
        verify_password_reset_token,
    )

    assert PASSWORD_RESET_PURPOSE == "password_reset"
    assert callable(create_password_reset_token)
    assert callable(verify_password_reset_token)
    assert callable(password_reset_timestamp)
    assert callable(create_password_reset_request)
    assert PasswordResetRequest is not None
