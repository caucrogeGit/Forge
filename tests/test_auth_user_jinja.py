"""Tests du contexte Jinja Auth/User et RBAC — AUTH-USER-JINJA-001."""

from __future__ import annotations

import inspect

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    AuthJinjaUser,
    get_jinja_current_user,
    make_auth_jinja_context,
    sanitize_jinja_user,
)
from core.auth.session import AUTH_USER_ID_SESSION_KEY
from core.auth.user import AuthUser
from forge_mvc_rbac.resolver import SELECT_USER_PERMISSIONS_SQL
from forge_mvc_rbac import make_can
from integrations.jinja2.renderer import Jinja2Renderer
from forge_mvc_testing import FakeRequest


def _authenticated_request(user_id: int = 42) -> FakeRequest:
    request = FakeRequest()
    request.session = {AUTH_USER_ID_SESSION_KEY: user_id}
    return request


def test_context_sans_utilisateur_expose_un_etat_anonyme():
    context = make_auth_jinja_context(FakeRequest())

    assert context["current_user"] is None
    assert context["is_authenticated"] is False
    assert context["can"]("article.create") is False


def test_context_authentifie_expose_un_utilisateur_minimal():
    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=lambda user_id, permission, **_: False,
    )

    assert context["is_authenticated"] is True
    assert context["current_user"] == AuthJinjaUser(id=7)


def test_loader_aware_orpheline_vue_non_authentifiee():
    # ADR-080 (F55) : avec un user_loader, une session orpheline (id sans compte)
    # est vue NON authentifiée par le provider Jinja, cohérent avec AuthMiddleware.
    context = make_auth_jinja_context(
        _authenticated_request(7),
        user_loader=lambda _uid: None,  # le compte n'existe plus
    )

    assert context["current_user"] is None
    assert context["is_authenticated"] is False


def test_loader_aware_sujet_existant_authentifie():
    from core.auth.user import AuthUser

    context = make_auth_jinja_context(
        _authenticated_request(7),
        user_loader=lambda uid: AuthUser(id=uid, email="u@x.fr", password_hash="x"),
    )

    assert context["is_authenticated"] is True
    assert context["current_user"] is not None


def test_can_true_si_permission_presente():
    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=lambda user_id, permission, **_: (
            user_id == 7 and permission == "article.create"
        ),
    )

    assert context["can"]("article.create") is True


def test_can_false_si_permission_absente():
    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=lambda user_id, permission, **_: False,
    )

    assert context["can"]("article.delete") is False


def test_can_false_pour_permission_inconnue():
    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=lambda user_id, permission, **_: False,
    )

    assert context["can"]("permission.inconnue") is False


def test_can_false_pour_utilisateur_sans_role():
    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=lambda user_id, permission, **_: False,
    )

    assert context["can"]("dashboard.view") is False


def test_can_false_pour_role_sans_permission():
    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=lambda user_id, permission, **_: False,
    )

    assert context["can"]("dashboard.view") is False


def test_can_false_si_resolver_indisponible_ou_mal_configure():
    def broken_checker(user_id, permission, **kwargs):
        raise RuntimeError("rbac indisponible")

    context = make_auth_jinja_context(
        _authenticated_request(7),
        permission_checker=broken_checker,
    )

    assert context["can"]("dashboard.view") is False


def test_can_resout_les_permissions_et_supprime_les_doublons():
    def fetch_all(sql, params):
        assert params == (7,)
        if sql == SELECT_USER_PERMISSIONS_SQL:
            return [
                {"code": "article.create"},
                {"code": "ARTICLE.CREATE"},
                {"code": "article.view"},
            ]
        return []

    context = make_auth_jinja_context(_authenticated_request(7), fetch_all=fetch_all)

    assert context["can"]("article.create") is True
    assert context["can"]("article.view") is True
    assert context["can"]("article.delete") is False


def test_can_garde_le_fallback_historique_sans_session_auth_user():
    request = FakeRequest()
    request.permissions = ["legacy.view"]
    context = make_auth_jinja_context(request, fallback_can=make_can(request))

    assert context["is_authenticated"] is False
    assert context["can"]("legacy.view") is True


def test_current_user_utilise_un_loader_si_fourni():
    request = _authenticated_request(9)

    user = get_jinja_current_user(
        request,
        user_loader=lambda user_id: {
            "id": user_id,
            "email": "ada@example.test",
            "password_hash": "secret",
            "is_active": True,
        },
    )

    assert user == AuthJinjaUser(id=9, email="ada@example.test", is_active=True)


def test_current_user_ne_fuit_pas_les_informations_sensibles():
    raw_user = AuthUser(
        id=3,
        email="user@example.test",
        password_hash="argon2-secret",
        is_active=True,
    )

    public_user = sanitize_jinja_user(raw_user)

    assert public_user == AuthJinjaUser(
        id=3,
        email="user@example.test",
        is_active=True,
    )
    assert not hasattr(public_user, "password_hash")
    assert "argon2-secret" not in repr(public_user)


def test_jinja_renderer_expose_des_globaux_surs_par_defaut(tmp_path):
    (tmp_path / "t.html").write_text(
        "{% if is_authenticated %}auth{% else %}anon{% endif %}:"
        "{{ current_user.id if current_user else 'none' }}:"
        "{% if can('article.create') %}can{% else %}no{% endif %}"
    )
    renderer = Jinja2Renderer(str(tmp_path))

    assert renderer.render("t.html", {}) == "anon:none:no"


def test_base_controller_injecte_current_user_is_authenticated_et_can(
    tmp_path,
    monkeypatch,
):
    import core.forge as forge
    from core.mvc.controller.base_controller import BaseController
    from core.templating.manager import template_manager

    monkeypatch.setattr(
        "forge_mvc_rbac.jinja.user_has_permission",
        lambda user_id, permission, **_: (
            user_id == 12 and permission == "article.create"
        ),
    )

    renderer = Jinja2Renderer(str(tmp_path))
    template_manager.register(renderer)
    forge._cfg["views_dir"] = str(tmp_path)

    (tmp_path / "t.html").write_text(
        "{% if is_authenticated %}auth{% else %}anon{% endif %}:"
        "{{ current_user.id if current_user else 'none' }}:"
        "{% if can('article.create') %}can{% else %}no{% endif %}"
    )

    response = BaseController.render(
        "t.html",
        context={},
        request=_authenticated_request(12),
    )

    assert b"auth:12:can" in response.body


def test_base_controller_preserve_can_historique_sans_auth_user(tmp_path):
    import core.forge as forge
    from core.mvc.controller.base_controller import BaseController
    from core.templating.manager import template_manager

    renderer = Jinja2Renderer(str(tmp_path))
    template_manager.register(renderer)
    forge._cfg["views_dir"] = str(tmp_path)

    (tmp_path / "t.html").write_text(
        "{% if is_authenticated %}auth{% else %}anon{% endif %}:"
        "{% if can('legacy.view') %}can{% else %}no{% endif %}"
    )
    request = FakeRequest()
    request.permissions = ["legacy.view"]

    response = BaseController.render("t.html", context={}, request=request)

    assert b"anon:can" in response.body


def test_module_jinja_ne_depend_pas_du_reseau_ni_de_librairie_externe():
    import forge_mvc_rbac.jinja as jinja_module

    src = inspect.getsource(jinja_module)
    for term in ("requests", "httpx", "urllib", "sqlalchemy"):
        assert term not in src


def test_module_jinja_ne_definit_pas_les_permissions_rbac():
    import forge_mvc_rbac.jinja as jinja_module

    src = inspect.getsource(jinja_module)
    assert "require_permission" not in src
    assert "role_permissions" not in src
