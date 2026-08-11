"""Tests AUTH-SESSION-002 — helpers d'authentification courants."""


import pytest

from core.auth import (
    AuthError,
    AuthUser,
    current_user,
    get_authenticated_user_id,
    hash_password,
    is_authenticated,
    login_required,
)
from core.http.response import Response


class FakeRequest:
    def __init__(self, session: dict | None = None):
        self.session = {} if session is None else session
        self.headers = {}


def _user(user_id: int = 1, *, active: bool = True) -> AuthUser:
    return AuthUser(
        id=user_id,
        login="admin@example.test",
        password_hash=hash_password("secret123"),
        is_active=active,
    )


def test_current_user_returns_none_without_session_id():
    request = FakeRequest()
    assert current_user(request, lambda user_id: _user(user_id)) is None


def test_current_user_calls_loader_with_session_id():
    request = FakeRequest({"_auth_user_id": 42})
    called = []

    current_user(request, lambda user_id: called.append(user_id) or _user(user_id))

    assert called == [42]


def test_current_user_returns_auth_user_from_loader():
    request = FakeRequest({"_auth_user_id": 1})
    user = _user()
    assert current_user(request, lambda user_id: user) == user


def test_current_user_returns_auth_user_from_dict():
    request = FakeRequest({"_auth_user_id": 1})
    password_hash = hash_password("secret123")

    user = current_user(
        request,
        lambda user_id: {
            "id": user_id,
            "login": "admin@example.test",
            "password_hash": password_hash,
            "is_active": True,
        },
    )

    assert isinstance(user, AuthUser)
    assert user.id == 1


def test_current_user_returns_none_if_loader_returns_none():
    request = FakeRequest({"_auth_user_id": 1})
    assert current_user(request, lambda user_id: None) is None


def test_current_user_returns_none_if_loader_data_invalid():
    request = FakeRequest({"_auth_user_id": 1})
    assert current_user(request, lambda user_id: {"id": user_id}) is None


def test_current_user_returns_none_if_user_inactive():
    request = FakeRequest({"_auth_user_id": 1})
    assert current_user(request, lambda user_id: _user(user_id, active=False)) is None


def test_current_user_refuses_non_callable_loader():
    with pytest.raises(AuthError, match="user_loader"):
        current_user(FakeRequest({"_auth_user_id": 1}), None)  # type: ignore[arg-type]


def test_current_user_does_not_modify_session():
    session = {"_auth_user_id": 1, "csrf_token": "csrf"}
    request = FakeRequest(session)
    current_user(request, lambda user_id: _user(user_id))
    assert request.session == session


def test_is_authenticated_false_without_session_auth():
    assert is_authenticated(FakeRequest()) is False


def test_is_authenticated_true_with_auth_user_id():
    assert is_authenticated(FakeRequest({"_auth_user_id": 1})) is True


def test_is_authenticated_false_with_invalid_id():
    assert get_authenticated_user_id(FakeRequest({"_auth_user_id": 0})) is None
    assert is_authenticated(FakeRequest({"_auth_user_id": 0})) is False


def test_login_required_allows_authenticated_request():
    request = FakeRequest({"_auth_user_id": 1})

    @login_required
    def dashboard(req):
        return Response(200, "ok")

    response = dashboard(request)
    assert response.status == 200
    assert response.body == b"ok"


def test_login_required_blocks_unauthenticated_request():
    @login_required
    def dashboard(request):
        return Response(200, "ok")

    response = dashboard(FakeRequest())
    assert response.status == 401
    assert b"Authentication required" in response.body


def test_login_required_factory_blocks_unauthenticated_request():
    @login_required()
    def dashboard(request):
        return Response(200, "ok")

    assert dashboard(FakeRequest()).status == 401


def test_login_required_can_redirect_when_explicit():
    @login_required(redirect_to="/connexion")
    def dashboard(request):
        return Response(200, "ok")

    response = dashboard(FakeRequest())
    assert response.status == 302
    assert response.headers["Location"] == "/connexion"


def test_login_required_preserves_decorated_function_arguments():
    request = FakeRequest({"_auth_user_id": 1})

    @login_required
    def show(req, item_id, *, mode="read"):
        return f"{item_id}:{mode}"

    assert show(request, 42, mode="edit") == "42:edit"


def test_login_required_preserves_function_metadata():
    @login_required
    def dashboard(request):
        """Dashboard doc."""
        return Response(200, "ok")

    assert dashboard.__name__ == "dashboard"
    assert dashboard.__doc__ == "Dashboard doc."


def test_public_import_from_core_auth():
    from core.auth import current_user as cu
    from core.auth import is_authenticated as ia
    from core.auth import login_required as lr

    assert callable(cu)
    assert callable(ia)
    assert callable(lr)


def test_no_login_logout_routes_created():
    import core.auth.session as session_module

    source = open(session_module.__file__, encoding="utf-8").read()
    assert "@route" not in source
    assert "def login(" not in source
    assert "def logout(" not in source


def test_no_form_or_template_created():
    import core.auth.session as session_module

    source = open(session_module.__file__, encoding="utf-8").read()
    assert "template" not in source.lower()
    assert "render" not in source.lower()


def test_no_rbac_change_or_permission_loading():
    import core.auth.session as session_module

    source = open(session_module.__file__, encoding="utf-8").read()
    assert "rbac" not in source.lower()
    assert "require_permission" not in source
    assert "permissions" not in source.lower()


def test_no_database_access(monkeypatch):
    import core.database.connection as connection_module

    calls = []
    if hasattr(connection_module, "get_connection"):
        monkeypatch.setattr(connection_module, "get_connection", lambda: calls.append(True))

    request = FakeRequest({"_auth_user_id": 1})
    assert current_user(request, lambda user_id: _user(user_id)).id == 1
    assert is_authenticated(request) is True
    assert calls == []
