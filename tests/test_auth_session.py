"""Tests AUTH-SESSION-001 — login/logout/session Auth/User."""

from types import SimpleNamespace

import pytest

from core.auth import (
    AuthError,
    AuthUser,
    authenticate_user,
    get_authenticated_user_id,
    hash_password,
    login_user,
    logout_user,
)


def _request(session: dict | None = None):
    return SimpleNamespace(session={} if session is None else session, headers={})


def _active_user(email: str = "admin@example.test") -> AuthUser:
    return AuthUser(
        id=1,
        email=email,
        password_hash=hash_password("secret123"),
        is_active=True,
    )


def test_authenticate_user_returns_auth_user_with_valid_credentials():
    expected = _active_user()

    user = authenticate_user(
        "admin@example.test",
        "secret123",
        lambda email: expected,
    )

    assert user == expected


def test_authenticate_user_accepts_normalizable_dict():
    password_hash = hash_password("secret123")

    user = authenticate_user(
        "admin@example.test",
        "secret123",
        lambda email: {
            "id": 1,
            "email": email,
            "password_hash": password_hash,
            "is_active": True,
        },
    )

    assert isinstance(user, AuthUser)
    assert user.email == "admin@example.test"


def test_authenticate_user_returns_none_if_loader_returns_none():
    assert authenticate_user("missing@example.test", "secret123", lambda email: None) is None


def test_authenticate_user_returns_none_if_password_is_wrong():
    user = _active_user()
    assert authenticate_user(user.email, "wrong", lambda email: user) is None


def test_authenticate_user_returns_none_if_user_inactive():
    inactive = AuthUser(
        id=1,
        email="admin@example.test",
        password_hash=hash_password("secret123"),
        is_active=False,
    )
    assert authenticate_user(inactive.email, "secret123", lambda email: inactive) is None


def test_authenticate_user_returns_none_if_loader_data_invalid():
    invalid = {"id": 1, "email": "admin@example.test"}
    assert authenticate_user("admin@example.test", "secret123", lambda email: invalid) is None


def test_authenticate_user_refuses_empty_email():
    assert authenticate_user("", "secret123", lambda email: _active_user()) is None


def test_authenticate_user_refuses_empty_password():
    assert authenticate_user("admin@example.test", "", lambda email: _active_user()) is None


def test_authenticate_user_refuses_non_callable_loader():
    with pytest.raises(AuthError, match="user_loader"):
        authenticate_user("admin@example.test", "secret123", None)  # type: ignore[arg-type]


def test_login_user_stores_only_user_id_in_session():
    request = _request()
    user = _active_user()

    login_user(request, user)

    assert request.session == {"_auth_user_id": user.id}


def test_login_user_does_not_store_email():
    request = _request()
    login_user(request, _active_user())
    assert "email" not in request.session


def test_login_user_does_not_store_password_hash():
    request = _request()
    login_user(request, _active_user())
    assert "password_hash" not in request.session


def test_login_user_does_not_store_auth_user_object():
    request = _request()
    login_user(request, _active_user())
    assert all(not isinstance(value, AuthUser) for value in request.session.values())


def test_login_user_preserves_existing_session_data():
    session = {"csrf_token": "csrf", "flash": {"message": "ok"}}
    request = _request(session)

    login_user(request, _active_user())

    assert request.session["csrf_token"] == "csrf"
    assert request.session["flash"] == {"message": "ok"}


def test_login_user_rejects_invalid_user():
    request = _request()
    with pytest.raises(AuthError):
        login_user(request, {"id": 1})  # type: ignore[arg-type]


def test_logout_user_removes_user_id_from_session():
    request = _request({"_auth_user_id": 1, "csrf_token": "csrf"})
    logout_user(request)
    assert "_auth_user_id" not in request.session
    assert request.session["csrf_token"] == "csrf"


def test_logout_user_is_idempotent():
    request = _request({"csrf_token": "csrf"})
    logout_user(request)
    logout_user(request)
    assert request.session == {"csrf_token": "csrf"}


def test_get_authenticated_user_id_returns_int():
    request = _request({"_auth_user_id": 42})
    assert get_authenticated_user_id(request) == 42


def test_get_authenticated_user_id_returns_none_without_user():
    assert get_authenticated_user_id(_request()) is None


def test_public_import_from_core_auth():
    from core.auth import authenticate_user as au
    from core.auth import get_authenticated_user_id as gaui
    from core.auth import login_user as lu
    from core.auth import logout_user as lou

    assert callable(au)
    assert callable(lu)
    assert callable(lou)
    assert callable(gaui)


def test_current_user_now_exists():
    import core.auth as auth

    assert hasattr(auth, "current_user")


def test_is_authenticated_now_exists():
    import core.auth as auth

    assert hasattr(auth, "is_authenticated")


def test_login_required_now_exists():
    import core.auth as auth

    assert hasattr(auth, "login_required")


def test_auth_session_does_not_access_database(monkeypatch):
    import core.database.connection as connection_module

    calls = []
    if hasattr(connection_module, "get_connection"):
        monkeypatch.setattr(connection_module, "get_connection", lambda: calls.append(True))

    user = _active_user()
    assert authenticate_user(user.email, "secret123", lambda email: user) == user
    login_user(_request(), user)
    assert calls == []


def test_auth_session_does_not_create_form_or_template():
    import core.auth.session as session_module

    source = open(session_module.__file__, encoding="utf-8").read()
    assert "form" not in source.lower()
    assert "template" not in source.lower()
    assert "render" not in source.lower()


def test_auth_session_does_not_modify_rbac():
    import core.auth.session as session_module

    source = open(session_module.__file__, encoding="utf-8").read()
    assert "rbac" not in source.lower()
    assert "require_permission" not in source
