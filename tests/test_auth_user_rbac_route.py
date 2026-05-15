"""Tests AUTH-USER-RBAC-ROUTE-001 — protection serveur Auth/User + RBAC."""

from __future__ import annotations

import inspect

from core.auth.session import AUTH_USER_ID_SESSION_KEY
from core.http.response import Response
import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import auth_user_can, make_can, require_permission, require_user_permission
from tests.fake_request import FakeRequest


def _request(user_id: int | None = 7) -> FakeRequest:
    request = FakeRequest()
    request.session = {}
    if user_id is not None:
        request.session[AUTH_USER_ID_SESSION_KEY] = user_id
    return request


def test_require_user_permission_allows_authenticated_user_with_permission():
    calls = []

    @require_user_permission(
        "article.edit",
        permission_checker=lambda user_id, permission, **_: calls.append(
            (user_id, permission)
        ) or True,
    )
    def controller(request):
        return Response(200, body=b"ok")

    response = controller(_request(42))

    assert response.status == 200
    assert response.body == b"ok"
    assert calls == [(42, "article.edit")]


def test_require_user_permission_returns_401_without_authenticated_user():
    called = False

    @require_user_permission(
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: True,
    )
    def controller(request):
        nonlocal called
        called = True
        return Response(200)

    response = controller(_request(None))

    assert response.status == 401
    assert b"Authentication required" in response.body
    assert called is False


def test_require_user_permission_returns_403_without_permission():
    called = False

    @require_user_permission(
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: False,
    )
    def controller(request):
        nonlocal called
        called = True
        return Response(200)

    response = controller(_request(7))

    assert response.status == 403
    assert b"Permission required: article.edit" in response.body
    assert called is False


def test_require_user_permission_normalizes_permission():
    calls = []

    @require_user_permission(
        "Article Edit",
        permission_checker=lambda user_id, permission, **_: calls.append(
            (user_id, permission)
        ) or True,
    )
    def controller(request):
        return Response(200)

    assert controller(_request(7)).status == 200
    assert calls == [(7, "article.edit")]


def test_require_user_permission_preserves_function_arguments_and_metadata():
    @require_user_permission(
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: True,
    )
    def controller(request, article_id, *, mode=None):
        """Controller doc."""
        return f"{article_id}:{mode}"

    assert controller.__name__ == "controller"
    assert controller.__doc__ == "Controller doc."
    assert controller(_request(7), 12, mode="draft") == "12:draft"


def test_require_user_permission_works_with_plain_controller_function():
    @require_user_permission(
        "dashboard.view",
        permission_checker=lambda user_id, permission, **_: (
            user_id == 3 and permission == "dashboard.view"
        ),
    )
    def dashboard(request):
        return {"ok": True}

    assert dashboard(_request(3)) == {"ok": True}


def test_require_user_permission_ignores_request_permissions():
    request = _request(7)
    request.permissions = ["article.edit"]

    @require_user_permission(
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: False,
    )
    def controller(request):
        return Response(200)

    assert controller(request).status == 403


def test_require_user_permission_ignores_legacy_session_permissions():
    request = _request(7)
    request.session["permissions"] = ["article.edit"]

    @require_user_permission(
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: False,
    )
    def controller(request):
        return Response(200)

    assert controller(request).status == 403


def test_auth_user_can_returns_true_when_permission_is_present():
    assert auth_user_can(
        _request(7),
        "Article Edit",
        permission_checker=lambda user_id, permission, **_: (
            user_id == 7 and permission == "article.edit"
        ),
    ) is True


def test_auth_user_can_returns_false_without_authenticated_user():
    assert auth_user_can(
        _request(None),
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: True,
    ) is False


def test_auth_user_can_returns_false_when_permission_is_absent():
    assert auth_user_can(
        _request(7),
        "article.edit",
        permission_checker=lambda *_args, **_kwargs: False,
    ) is False


def test_api_importable_from_forge_mvc_rbac():
    import forge_mvc_rbac

    assert forge_mvc_rbac.require_user_permission is require_user_permission
    assert forge_mvc_rbac.auth_user_can is auth_user_can


def test_does_not_modify_historic_require_permission_or_make_can():
    import forge_mvc_rbac.rbac as rbac_module

    require_source = inspect.getsource(rbac_module.require_permission)
    make_can_source = inspect.getsource(rbac_module.make_can)

    assert "get_authenticated_user_id" not in require_source
    assert "user_has_permission" not in require_source
    assert "user_roles" not in require_source
    assert "get_authenticated_user_id" not in make_can_source
    assert "user_has_permission" not in make_can_source
    assert "user_roles" not in make_can_source
    assert callable(require_permission)
    assert callable(make_can)


def test_does_not_modify_jinja_can():
    import forge_mvc_rbac.jinja as auth_jinja

    source = inspect.getsource(auth_jinja)
    assert "require_user_permission" not in source


def test_no_direct_db_write_route_or_admin_surface():
    import forge_mvc_rbac.authorization as authorization

    source = inspect.getsource(authorization)
    for forbidden in (
        "INSERT INTO",
        "UPDATE ",
        "DELETE ",
        "@route",
        "def route",
        "admin",
        "CREATE TABLE",
    ):
        assert forbidden not in source
