"""Tests AUTH-RESET-002 — reinitialisation effective du mot de passe."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.auth import (
    PasswordResetResult,
    reset_password_with_token,
    validate_new_password,
    verify_password,
)
from core.auth.exceptions import InvalidNewPasswordError
from core.auth.reset import (
    PASSWORD_RESET_PURPOSE,
    PasswordResetRequest,
    create_password_reset_request,
    create_password_reset_token,
    password_reset_timestamp,
    verify_password_reset_token,
)
from core.auth.tokens import AuthToken, hash_auth_token
from core.auth.user import AuthUser


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_valid_token(*, minutes: int = 30, used: bool = False):
    now = datetime.now(tz=timezone.utc)
    raw_token, _ = create_password_reset_token(user_id=1, now=now)
    token_hash = hash_auth_token(raw_token)
    expires_at = now + timedelta(minutes=minutes)
    used_at = now if used else None
    token_record = AuthToken(
        user_id=1,
        purpose=PASSWORD_RESET_PURPOSE,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=used_at,
    )
    return raw_token, token_record


# ---------------------------------------------------------------------------
# validate_new_password
# ---------------------------------------------------------------------------


def test_validate_new_password_accepts_valid():
    assert validate_new_password("motdepasse") is None


def test_validate_new_password_raises_on_empty():
    with pytest.raises(InvalidNewPasswordError):
        validate_new_password("")


def test_validate_new_password_raises_on_none():
    with pytest.raises(InvalidNewPasswordError):
        validate_new_password(None)  # type: ignore[arg-type]


def test_validate_new_password_raises_on_non_string():
    with pytest.raises(InvalidNewPasswordError):
        validate_new_password(12345)  # type: ignore[arg-type]


def test_validate_new_password_raises_on_too_short():
    with pytest.raises(InvalidNewPasswordError):
        validate_new_password("court")


def test_validate_new_password_accepts_exactly_min_length():
    assert validate_new_password("abcdefgh") is None


# ---------------------------------------------------------------------------
# reset_password_with_token — cas valides
# ---------------------------------------------------------------------------


def test_reset_returns_result_with_valid_token():
    raw_token, token_record = _make_valid_token()
    result = reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert isinstance(result, PasswordResetResult)


def test_reset_result_contains_user_id():
    raw_token, token_record = _make_valid_token()
    result = reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert result.user_id == token_record.user_id


def test_reset_result_contains_password_hash():
    raw_token, token_record = _make_valid_token()
    result = reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert isinstance(result.password_hash, str)
    assert result.password_hash


def test_reset_result_password_hash_does_not_contain_plaintext():
    new_password = "nouveau_mdp_ok"
    raw_token, token_record = _make_valid_token()
    result = reset_password_with_token(raw_token, token_record, new_password)
    assert new_password not in result.password_hash


def test_reset_result_password_hash_verifiable():
    new_password = "nouveau_mdp_ok"
    raw_token, token_record = _make_valid_token()
    result = reset_password_with_token(raw_token, token_record, new_password)
    assert verify_password(new_password, result.password_hash) is True


def test_reset_result_contains_used_at():
    raw_token, token_record = _make_valid_token()
    result = reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert isinstance(result.used_at, datetime)


def test_reset_accepts_dict_token_record():
    raw_token, token_record = _make_valid_token()
    data = {
        "user_id": token_record.user_id,
        "purpose": token_record.purpose,
        "token_hash": token_record.token_hash,
        "expires_at": token_record.expires_at,
        "used_at": token_record.used_at,
    }
    result = reset_password_with_token(raw_token, data, "nouveau_mdp_ok")
    assert result is not None
    assert isinstance(result, PasswordResetResult)


# ---------------------------------------------------------------------------
# reset_password_with_token — token invalide → None
# ---------------------------------------------------------------------------


def test_reset_returns_none_with_wrong_token():
    _, token_record = _make_valid_token()
    result = reset_password_with_token("mauvais-token", token_record, "nouveau_mdp_ok")
    assert result is None


def test_reset_returns_none_with_expired_token():
    raw_token, token_record = _make_valid_token(minutes=-1)
    result = reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert result is None


def test_reset_returns_none_with_used_token():
    raw_token, token_record = _make_valid_token(used=True)
    result = reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert result is None


def test_reset_returns_none_with_wrong_purpose():
    now = datetime.now(tz=timezone.utc)
    raw_token, _ = create_password_reset_token(user_id=1, now=now)
    token_hash = hash_auth_token(raw_token)
    bad_record = AuthToken(
        user_id=1,
        purpose="email_verification",
        token_hash=token_hash,
        expires_at=now + timedelta(minutes=30),
        used_at=None,
    )
    result = reset_password_with_token(raw_token, bad_record, "nouveau_mdp_ok")
    assert result is None


def test_reset_returns_none_with_invalid_record():
    raw_token, _ = _make_valid_token()
    assert reset_password_with_token(raw_token, None, "nouveau_mdp_ok") is None
    assert reset_password_with_token(raw_token, {}, "nouveau_mdp_ok") is None
    assert reset_password_with_token(raw_token, 42, "nouveau_mdp_ok") is None


# ---------------------------------------------------------------------------
# reset_password_with_token — mot de passe invalide → exception
# ---------------------------------------------------------------------------


def test_reset_raises_on_empty_password():
    raw_token, token_record = _make_valid_token()
    with pytest.raises(InvalidNewPasswordError):
        reset_password_with_token(raw_token, token_record, "")


def test_reset_raises_on_none_password():
    raw_token, token_record = _make_valid_token()
    with pytest.raises(InvalidNewPasswordError):
        reset_password_with_token(raw_token, token_record, None)  # type: ignore[arg-type]


def test_reset_raises_on_non_string_password():
    raw_token, token_record = _make_valid_token()
    with pytest.raises(InvalidNewPasswordError):
        reset_password_with_token(raw_token, token_record, 12345)  # type: ignore[arg-type]


def test_reset_raises_on_short_password():
    raw_token, token_record = _make_valid_token()
    with pytest.raises(InvalidNewPasswordError):
        reset_password_with_token(raw_token, token_record, "court")


# ---------------------------------------------------------------------------
# Immutabilite — rien n'est modifie
# ---------------------------------------------------------------------------


def test_reset_does_not_modify_token_record():
    raw_token, token_record = _make_valid_token()
    original_hash = token_record.token_hash
    original_used_at = token_record.used_at
    reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert token_record.token_hash == original_hash
    assert token_record.used_at == original_used_at


def test_reset_does_not_set_used_at_on_token_record():
    raw_token, token_record = _make_valid_token()
    reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert token_record.used_at is None


# ---------------------------------------------------------------------------
# Compatibilite — fonctions AUTH-RESET-001 toujours operationnelles
# ---------------------------------------------------------------------------


def test_create_password_reset_token_still_works():
    raw_token, auth_token = create_password_reset_token(user_id=1)
    assert isinstance(raw_token, str)
    assert auth_token.purpose == PASSWORD_RESET_PURPOSE


def test_verify_password_reset_token_still_works():
    raw_token, token_record = _make_valid_token()
    assert verify_password_reset_token(raw_token, token_record) is True


def test_password_reset_timestamp_still_works():
    ts = password_reset_timestamp()
    assert isinstance(ts, datetime)


def test_create_password_reset_request_still_works():
    user = AuthUser(id=1, email="a@b.com", password_hash="h" * 10)
    req = create_password_reset_request(user)
    assert isinstance(req, PasswordResetRequest)


# ---------------------------------------------------------------------------
# Perimetres exclus
# ---------------------------------------------------------------------------


def test_no_session_created(monkeypatch):
    calls = []
    import core.security.session as session_module
    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")
    raw_token, token_record = _make_valid_token()
    reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert calls == []


def test_no_database_access(monkeypatch):
    calls = []
    monkeypatch.setattr("mariadb.connect", lambda *a, **kw: calls.append(True), raising=False)
    raw_token, token_record = _make_valid_token()
    reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert calls == []


def test_no_mail_sent(monkeypatch):
    sent = []
    monkeypatch.setattr("smtplib.SMTP", lambda *a, **kw: sent.append(True), raising=False)
    raw_token, token_record = _make_valid_token()
    reset_password_with_token(raw_token, token_record, "nouveau_mdp_ok")
    assert sent == []


def test_api_importable_from_core_auth():
    from core.auth import (
        InvalidNewPasswordError,
        PasswordResetResult,
        reset_password_with_token,
        validate_new_password,
    )
    assert callable(reset_password_with_token)
    assert callable(validate_new_password)
    assert PasswordResetResult is not None
    assert issubclass(InvalidNewPasswordError, ValueError)
