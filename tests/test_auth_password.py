"""Tests AUTH-PASSWORD-001 — hachage Auth/User."""

from dataclasses import fields

import pytest

from core.auth import (
    AuthError,
    AuthUser,
    hash_password,
    password_needs_rehash,
    verify_password,
)


def test_hash_password_returns_string():
    password_hash = hash_password("secret123")
    assert isinstance(password_hash, str)
    assert password_hash


def test_hash_password_does_not_contain_plain_password():
    password_hash = hash_password("secret123")
    assert "secret123" not in password_hash


def test_hash_password_uses_salt():
    assert hash_password("secret123") != hash_password("secret123")


def test_verify_password_true_with_matching_password():
    password_hash = hash_password("secret123")
    assert verify_password("secret123", password_hash) is True


def test_verify_password_false_with_wrong_password():
    password_hash = hash_password("secret123")
    assert verify_password("bad-password", password_hash) is False


def test_verify_password_false_with_invalid_hash():
    assert verify_password("secret123", "not-an-argon2-hash") is False


def test_hash_password_rejects_empty_password():
    with pytest.raises(AuthError, match="password"):
        hash_password("")


def test_hash_password_rejects_none():
    with pytest.raises(AuthError, match="password"):
        hash_password(None)  # type: ignore[arg-type]


def test_verify_password_false_with_empty_password():
    password_hash = hash_password("secret123")
    assert verify_password("", password_hash) is False


def test_verify_password_false_with_none_password():
    password_hash = hash_password("secret123")
    assert verify_password(None, password_hash) is False  # type: ignore[arg-type]


def test_verify_password_false_with_empty_hash():
    assert verify_password("secret123", "") is False


def test_verify_password_false_with_none_hash():
    assert verify_password("secret123", None) is False  # type: ignore[arg-type]


def test_password_needs_rehash_returns_bool():
    password_hash = hash_password("secret123")
    assert isinstance(password_needs_rehash(password_hash), bool)


def test_password_needs_rehash_false_with_invalid_hash():
    assert password_needs_rehash("not-an-argon2-hash") is False


def test_public_import_from_core_auth():
    from core.auth import hash_password as hp
    from core.auth import password_needs_rehash as pnr
    from core.auth import verify_password as vp

    assert callable(hp)
    assert callable(vp)
    assert callable(pnr)


def test_password_api_does_not_access_database(monkeypatch):
    import core.database.connection as connection_module

    calls = []
    if hasattr(connection_module, "get_connection"):
        monkeypatch.setattr(connection_module, "get_connection", lambda: calls.append(True))

    password_hash = hash_password("secret123")
    assert verify_password("secret123", password_hash) is True
    assert password_needs_rehash(password_hash) is False
    assert calls == []


def test_password_api_does_not_create_session(monkeypatch):
    import core.security.session as session_module

    calls = []
    monkeypatch.setattr(session_module, "create_session", lambda: calls.append(True) or "fake")

    password_hash = hash_password("secret123")
    verify_password("secret123", password_hash)

    assert calls == []


def test_password_ticket_does_not_create_advanced_auth_features():
    import core.auth as auth

    for name in (
        "reset_password",
        "verify_email",
        "create_token",
        "user_roles",
    ):
        assert not hasattr(auth, name)


def test_auth_user_contract_est_fige():
    """Le contrat est figé, et il a changé une fois, par décision (ADR-089).

    `email` portait l'identité et le contact à la fois. Il porte maintenant le
    seul contact, facultatif, et `login` porte l'identité. Ce test n'affirme
    pas que le contrat ne bouge jamais, mais qu'il ne bouge pas sans qu'on
    l'écrive ici.
    """
    assert [field.name for field in fields(AuthUser)] == [
        "id",
        "login",
        "password_hash",
        "is_active",
        "email",
        "created_at",
        "updated_at",
    ]


def test_users_sql_stays_unchanged_for_password_ticket():
    # AUTH-DDL-TESTS-SOURCE-001 : lit la constante canonique et non la fixture,
    # qui n'est qu'une copie (tenue par `test_auth_ddl_fixture_parity_001`).
    from cli.security.auth import USERS_SQL

    sql = USERS_SQL
    assert "password_hash VARCHAR(255) NOT NULL" in sql
    assert "CREATE TABLE IF NOT EXISTS users" in sql
    assert "INSERT INTO users" not in sql
