"""Tests du décorateur require_permission et helpers d'autorisation — AUTH-RBAC-002."""

from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    PermissionDenied,
    RbacValidationError,
    get_request_permissions,
    has_permission,
    require_permission,
)
from forge_mvc_testing import FakeRequest


# ---------------------------------------------------------------------------
# PermissionDenied
# ---------------------------------------------------------------------------


def test_permission_denied_est_exception():
    assert issubclass(PermissionDenied, Exception)


def test_permission_denied_peut_etre_levee():
    with pytest.raises(PermissionDenied):
        raise PermissionDenied("interdit")


# ---------------------------------------------------------------------------
# get_request_permissions — injection directe
# ---------------------------------------------------------------------------


def test_get_permissions_vide_sans_session():
    req = FakeRequest()
    assert get_request_permissions(req) == set()


def test_get_permissions_via_injection():
    req = FakeRequest()
    req.permissions = ["posts.edit", "posts.view"]
    assert get_request_permissions(req) == {"posts.edit", "posts.view"}


def test_get_permissions_injection_vide():
    req = FakeRequest()
    req.permissions = []
    assert get_request_permissions(req) == set()


def test_get_permissions_retourne_set():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    result = get_request_permissions(req)
    assert isinstance(result, set)


def test_get_permissions_deduplique():
    req = FakeRequest()
    req.permissions = ["posts.edit", "posts.edit"]
    assert get_request_permissions(req) == {"posts.edit"}


# ---------------------------------------------------------------------------
# get_request_permissions — depuis la session
# ---------------------------------------------------------------------------


def test_get_permissions_depuis_session():
    from core.sessions.manager import get_session_store
    from core.security.session import create_session, delete_session

    session_id = create_session()
    get_session_store().set(session_id, {
        "authenticated": True,
        "user": {
            "id": 1, "login": "test", "prenom": "", "nom": "", "email": "",
            "roles": [], "permissions": ["articles.publish", "users.view"],
        },
    })

    req = FakeRequest(session_id=session_id)
    perms = get_request_permissions(req)
    assert perms == {"articles.publish", "users.view"}

    delete_session(session_id)


def test_get_permissions_session_sans_permissions():
    from core.sessions.manager import get_session_store
    from core.security.session import create_session, delete_session

    session_id = create_session()
    get_session_store().set(session_id, {
        "authenticated": True,
        "user": {
            "id": 1, "login": "test", "prenom": "", "nom": "", "email": "",
            "roles": ["admin"],
        },
    })

    req = FakeRequest(session_id=session_id)
    assert get_request_permissions(req) == set()

    delete_session(session_id)


# ---------------------------------------------------------------------------
# has_permission
# ---------------------------------------------------------------------------


def test_has_permission_vrai():
    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert has_permission(req, "posts.edit") is True


def test_has_permission_faux():
    req = FakeRequest()
    req.permissions = ["posts.view"]
    assert has_permission(req, "posts.edit") is False


def test_has_permission_sans_permissions():
    req = FakeRequest()
    assert has_permission(req, "posts.edit") is False


# ---------------------------------------------------------------------------
# require_permission — validation à la décoration
# ---------------------------------------------------------------------------


def test_require_permission_valide_code_vide():
    with pytest.raises(RbacValidationError):
        require_permission("")


def test_require_permission_valide_code_sans_point():
    with pytest.raises(RbacValidationError):
        require_permission("postsedit")


def test_require_permission_valide_code_avec_espace():
    with pytest.raises(RbacValidationError):
        require_permission("posts edit")


# ---------------------------------------------------------------------------
# require_permission — comportement à l'exécution
# ---------------------------------------------------------------------------


def test_require_permission_403_si_absent():
    @require_permission("posts.edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    response = action(req)
    assert response.status == 403


def test_require_permission_corps_403():
    @require_permission("posts.edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    response = action(req)
    assert b"posts.edit" in response.body


def test_require_permission_laisse_passer_si_present():
    @require_permission("posts.edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert action(req) == "ok"


def test_require_permission_normalise_le_code():
    @require_permission("Posts.Edit")
    def action(request):
        return "ok"

    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert action(req) == "ok"


def test_require_permission_transmet_args():
    @require_permission("posts.edit")
    def action(request, item_id):
        return item_id

    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert action(req, 42) == 42


def test_require_permission_transmet_kwargs():
    @require_permission("posts.edit")
    def action(request, item_id=None):
        return item_id

    req = FakeRequest()
    req.permissions = ["posts.edit"]
    assert action(req, item_id=7) == 7


# ---------------------------------------------------------------------------
# functools.wraps
# ---------------------------------------------------------------------------


def test_require_permission_preserve_nom():
    @require_permission("posts.edit")
    def mon_action(request):
        return "ok"

    assert mon_action.__name__ == "mon_action"


def test_require_permission_preserve_doc():
    @require_permission("posts.edit")
    def mon_action(request):
        """Docstring test."""
        return "ok"

    assert mon_action.__doc__ == "Docstring test."


# ---------------------------------------------------------------------------
# Absence de dépendance métier
# ---------------------------------------------------------------------------


def test_autorisation_sans_terme_metier():
    import inspect
    import forge_mvc_rbac.rbac as rbac_module
    src = inspect.getsource(rbac_module)
    for term in ("commune", "sejour", "hebergement", "reservation"):
        assert term not in src.lower(), f"Terme métier '{term}' détecté dans rbac.py"
