"""Tests AUTH-EMAIL-001 — verification d'adresse email."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.auth import (
    EMAIL_VERIFICATION_PURPOSE,
    create_email_verification_token,
    email_verification_timestamp,
    is_email_verified,
    verify_email_verification_token,
)
from core.auth.exceptions import AuthError
from core.auth.tokens import AuthToken


# ---------------------------------------------------------------------------
# Constante PURPOSE
# ---------------------------------------------------------------------------


def test_email_verification_purpose_value():
    assert EMAIL_VERIFICATION_PURPOSE == "email_verification"


# ---------------------------------------------------------------------------
# create_email_verification_token
# ---------------------------------------------------------------------------


def test_create_returns_tuple_str_and_auth_token():
    raw_token, auth_token = create_email_verification_token(user_id=1)
    assert isinstance(raw_token, str)
    assert isinstance(auth_token, AuthToken)


def test_create_token_brut_differs_from_hash():
    raw_token, auth_token = create_email_verification_token(user_id=1)
    assert raw_token != auth_token.token_hash


def test_create_auth_token_user_id():
    _, auth_token = create_email_verification_token(user_id=42)
    assert auth_token.user_id == 42


def test_create_auth_token_purpose():
    _, auth_token = create_email_verification_token(user_id=1)
    assert auth_token.purpose == EMAIL_VERIFICATION_PURPOSE


def test_create_auth_token_expires_at_is_future():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_email_verification_token(user_id=1, now=now)
    assert auth_token.expires_at > now


def test_create_auth_token_used_at_is_none():
    _, auth_token = create_email_verification_token(user_id=1)
    assert auth_token.used_at is None


def test_create_auth_token_created_at_is_set():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_email_verification_token(user_id=1, now=now)
    assert auth_token.created_at == now


def test_create_custom_minutes():
    now = datetime.now(tz=timezone.utc)
    _, auth_token = create_email_verification_token(user_id=1, minutes=30, now=now)
    assert auth_token.expires_at == now + timedelta(minutes=30)


def test_create_two_tokens_differ():
    raw1, _ = create_email_verification_token(user_id=1)
    raw2, _ = create_email_verification_token(user_id=1)
    assert raw1 != raw2


def test_create_refuses_user_id_zero():
    with pytest.raises(AuthError):
        create_email_verification_token(user_id=0)


def test_create_refuses_user_id_negative():
    with pytest.raises(AuthError):
        create_email_verification_token(user_id=-1)


def test_create_refuses_user_id_string():
    with pytest.raises(AuthError):
        create_email_verification_token(user_id="1")  # type: ignore[arg-type]


def test_create_refuses_user_id_bool():
    with pytest.raises(AuthError):
        create_email_verification_token(user_id=True)


def test_create_refuses_minutes_zero():
    with pytest.raises(AuthError):
        create_email_verification_token(user_id=1, minutes=0)


def test_create_refuses_minutes_negative():
    with pytest.raises(AuthError):
        create_email_verification_token(user_id=1, minutes=-10)


# ---------------------------------------------------------------------------
# verify_email_verification_token
# ---------------------------------------------------------------------------


def _make_token(*, minutes_offset: int = 60, used: bool = False, purpose: str = EMAIL_VERIFICATION_PURPOSE):
    now = datetime.now(tz=timezone.utc)
    expires_at = now + timedelta(minutes=minutes_offset)
    used_at = now if used else None
    raw_token, _ = create_email_verification_token(user_id=1, now=now)
    from core.auth.tokens import hash_auth_token
    from core.auth.tokens import AuthToken as _AuthToken
    token_hash = hash_auth_token(raw_token)
    token_record = _AuthToken(
        user_id=1,
        purpose=purpose,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=used_at,
    )
    return raw_token, token_record


def test_verify_returns_true_with_valid_token():
    raw_token, token_record = _make_token()
    assert verify_email_verification_token(raw_token, token_record) is True


def test_verify_accepts_dict():
    raw_token, token_record = _make_token()
    data = {
        "user_id": token_record.user_id,
        "purpose": token_record.purpose,
        "token_hash": token_record.token_hash,
        "expires_at": token_record.expires_at,
        "used_at": token_record.used_at,
    }
    assert verify_email_verification_token(raw_token, data) is True


def test_verify_returns_false_with_wrong_token():
    _, token_record = _make_token()
    assert verify_email_verification_token("wrong-token", token_record) is False


def test_verify_returns_false_with_empty_token():
    _, token_record = _make_token()
    assert verify_email_verification_token("", token_record) is False


def test_verify_returns_false_if_expired():
    raw_token, token_record = _make_token(minutes_offset=-1)
    assert verify_email_verification_token(raw_token, token_record) is False


def test_verify_returns_false_if_used():
    raw_token, token_record = _make_token(used=True)
    assert verify_email_verification_token(raw_token, token_record) is False


def test_verify_returns_false_if_wrong_purpose():
    raw_token, token_record = _make_token(purpose="reset-password")
    assert verify_email_verification_token(raw_token, token_record) is False


def test_verify_returns_false_with_invalid_record():
    raw_token, _ = _make_token()
    assert verify_email_verification_token(raw_token, None) is False
    assert verify_email_verification_token(raw_token, {}) is False
    assert verify_email_verification_token(raw_token, "not-a-token") is False


def test_verify_does_not_modify_token_record():
    raw_token, token_record = _make_token()
    verify_email_verification_token(raw_token, token_record)
    assert token_record.used_at is None


# ---------------------------------------------------------------------------
# email_verification_timestamp
# ---------------------------------------------------------------------------


def test_email_verification_timestamp_returns_datetime():
    ts = email_verification_timestamp()
    assert isinstance(ts, datetime)


def test_email_verification_timestamp_accepts_now():
    now = datetime.now(tz=timezone.utc)
    assert email_verification_timestamp(now=now) == now


def test_email_verification_timestamp_default_is_utc():
    ts = email_verification_timestamp()
    assert ts.tzinfo is not None


# ---------------------------------------------------------------------------
# is_email_verified
# ---------------------------------------------------------------------------


def test_is_email_verified_false_with_none():
    assert is_email_verified(None) is False


def test_is_email_verified_true_with_datetime():
    assert is_email_verified(datetime.now(tz=timezone.utc)) is True


def test_is_email_verified_true_with_any_truthy_value():
    assert is_email_verified(datetime(2025, 1, 1)) is True


# ---------------------------------------------------------------------------
# Imports publics depuis core.auth
# ---------------------------------------------------------------------------


def test_api_importable_from_core_auth():
    from core.auth import (
        EMAIL_VERIFICATION_PURPOSE,
        create_email_verification_token,
        email_verification_timestamp,
        is_email_verified,
        verify_email_verification_token,
    )

    assert EMAIL_VERIFICATION_PURPOSE == "email_verification"
    assert callable(create_email_verification_token)
    assert callable(verify_email_verification_token)
    assert callable(email_verification_timestamp)
    assert callable(is_email_verified)


# ---------------------------------------------------------------------------
# Perimetres exclus
# ---------------------------------------------------------------------------


def test_no_mail_sent(monkeypatch):
    sent = []
    monkeypatch.setattr("smtplib.SMTP", lambda *a, **kw: sent.append(True), raising=False)
    create_email_verification_token(user_id=1)
    assert sent == []


def test_no_session_created(monkeypatch):
    calls = []
    import core.security.session as session_module
    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")
    create_email_verification_token(user_id=1)
    assert calls == []


def test_no_database_access(monkeypatch):
    calls = []
    monkeypatch.setattr("mariadb.connect", lambda *a, **kw: calls.append(True), raising=False)
    create_email_verification_token(user_id=1)
    assert calls == []


def test_users_sql_still_contains_email_verified_at():
    from pathlib import Path
    sql = Path("tests/fixtures/app/mvc/models/sql/users.sql").read_text(encoding="utf-8")
    assert "email_verified_at DATETIME NULL" in sql


def test_auth_tokens_sql_unchanged():
    from pathlib import Path
    sql = Path("tests/fixtures/app/mvc/models/sql/auth_tokens.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS auth_tokens" in sql
    assert "token_hash CHAR(64) NOT NULL UNIQUE" in sql
