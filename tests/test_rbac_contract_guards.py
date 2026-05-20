"""Tests — RBAC-MODULE-005 : guards opt-in pour routes et contrôleurs.

Vérifie get_request_roles, require_contract_permission_for_request et
contract_permission_required. Ces helpers sont opt-in : le développeur les
applique explicitement. make:crud core reste neutre.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    get_request_roles,
    require_contract_permission_for_request,
    contract_permission_required,
    load_rbac_contract,
    has_permission,
    require_permission,
)
from core.http.response import Response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_CONTRACT_DATA = {
    "schema_version": "1.0",
    "roles": {
        "admin": ["article.list", "article.create", "article.update", "article.delete"],
        "editor": ["article.list", "article.update"],
        "reader": ["article.list"],
    },
}


def _write_rbac(tmp_path: Path, content: dict) -> None:
    d = tmp_path / "mvc" / "security"
    d.mkdir(parents=True)
    (d / "rbac.json").write_text(json.dumps(content), encoding="utf-8")


class _Request:
    """Fausse requête avec injection de rôles."""

    def __init__(self, roles=None):
        if roles is not None:
            self.roles = roles


class _RequestNoRoles:
    """Fausse requête sans attribut roles ni session."""
    pass


# ---------------------------------------------------------------------------
# Imports publics
# ---------------------------------------------------------------------------


def test_import_get_request_roles():
    from forge_mvc_rbac import get_request_roles as _f
    assert callable(_f)


def test_import_require_contract_permission_for_request():
    from forge_mvc_rbac import require_contract_permission_for_request as _f
    assert callable(_f)


def test_import_contract_permission_required():
    from forge_mvc_rbac import contract_permission_required as _f
    assert callable(_f)


# ---------------------------------------------------------------------------
# get_request_roles
# ---------------------------------------------------------------------------


def test_roles_injected_list():
    assert get_request_roles(_Request(roles=["admin"])) == ["admin"]


def test_roles_injected_empty():
    assert get_request_roles(_Request(roles=[])) == []


def test_roles_no_attribute():
    assert get_request_roles(_RequestNoRoles()) == []


def test_roles_injected_filters_non_strings():
    class R:
        roles = ["admin", 42, None, "reader"]
    assert get_request_roles(R()) == ["admin", "reader"]


def test_roles_injected_not_a_list():
    class R:
        roles = "admin"
    assert get_request_roles(R()) == []


# ---------------------------------------------------------------------------
# require_contract_permission_for_request — sans contrat (absent)
# ---------------------------------------------------------------------------


def test_no_contract_returns_403(tmp_path):
    resp = require_contract_permission_for_request(_Request(roles=["admin"]), "article.list", tmp_path)
    assert isinstance(resp, Response)
    assert resp.status == 403


def test_no_session_returns_403(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(_RequestNoRoles(), "article.list", tmp_path)
    assert isinstance(resp, Response)
    assert resp.status == 403


def test_empty_roles_returns_403(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(_Request(roles=[]), "article.list", tmp_path)
    assert isinstance(resp, Response)
    assert resp.status == 403


# ---------------------------------------------------------------------------
# require_contract_permission_for_request — rôle autorisé
# ---------------------------------------------------------------------------


def test_admin_allowed(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(_Request(roles=["admin"]), "article.delete", tmp_path)
    assert resp is None


def test_reader_allowed_list(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(_Request(roles=["reader"]), "article.list", tmp_path)
    assert resp is None


# ---------------------------------------------------------------------------
# require_contract_permission_for_request — rôle non autorisé
# ---------------------------------------------------------------------------


def test_reader_denied_delete(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(_Request(roles=["reader"]), "article.delete", tmp_path)
    assert isinstance(resp, Response)
    assert resp.status == 403


def test_unknown_role_denied(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(_Request(roles=["unknown"]), "article.list", tmp_path)
    assert isinstance(resp, Response)
    assert resp.status == 403


# ---------------------------------------------------------------------------
# require_contract_permission_for_request — rôles multiples
# ---------------------------------------------------------------------------


def test_multi_roles_allowed_if_one_has_permission(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(
        _Request(roles=["reader", "admin"]), "article.delete", tmp_path
    )
    assert resp is None


def test_multi_roles_denied_if_none_has_permission(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    resp = require_contract_permission_for_request(
        _Request(roles=["reader", "editor"]), "article.delete", tmp_path
    )
    assert isinstance(resp, Response)
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Contrat invalide
# ---------------------------------------------------------------------------


def test_invalid_contract_returns_403(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "2.0"})
    resp = require_contract_permission_for_request(_Request(roles=["admin"]), "article.list", tmp_path)
    assert isinstance(resp, Response)
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Helper ne modifie pas la requête
# ---------------------------------------------------------------------------


def test_request_not_modified(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    req = _Request(roles=["admin"])
    roles_before = req.roles[:]
    require_contract_permission_for_request(req, "article.list", tmp_path)
    assert req.roles == roles_before


# ---------------------------------------------------------------------------
# contract_permission_required — décorateur
# ---------------------------------------------------------------------------


def test_decorator_allows_call(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)
    called = []

    @contract_permission_required("article.delete", project_root=tmp_path)
    def delete(request):
        called.append(True)
        return "ok"

    result = delete(_Request(roles=["admin"]))
    assert result == "ok"
    assert called


def test_decorator_blocks_with_403(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)

    @contract_permission_required("article.delete", project_root=tmp_path)
    def delete(request):
        return "ok"

    result = delete(_Request(roles=["reader"]))
    assert isinstance(result, Response)
    assert result.status == 403


def test_decorator_blocks_no_roles(tmp_path):
    _write_rbac(tmp_path, _CONTRACT_DATA)

    @contract_permission_required("article.list", project_root=tmp_path)
    def index(request):
        return "ok"

    result = index(_RequestNoRoles())
    assert isinstance(result, Response)
    assert result.status == 403


def test_decorator_preserves_function_name(tmp_path):
    @contract_permission_required("article.list", project_root=tmp_path)
    def my_action(request):
        return "ok"

    assert my_action.__name__ == "my_action"


# ---------------------------------------------------------------------------
# make:crud non importé dans le module RBAC
# ---------------------------------------------------------------------------


def test_make_crud_not_in_contract_source():
    from pathlib import Path
    src = (Path(__file__).parents[1] / "packages" / "forge-mvc-rbac" / "forge_mvc_rbac" / "contract.py")
    assert "make_crud" not in src.read_text(encoding="utf-8")


def test_make_crud_not_in_init_source():
    from pathlib import Path
    src = (Path(__file__).parents[1] / "packages" / "forge-mvc-rbac" / "forge_mvc_rbac" / "__init__.py")
    assert "make_crud" not in src.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Pas de régression sur l'API existante
# ---------------------------------------------------------------------------


def test_has_permission_unchanged():
    class FakeRequest:
        permissions = {"article.list"}

    assert has_permission(FakeRequest(), "article.list") is True


def test_require_permission_unchanged():
    decorator = require_permission("article.list")
    assert callable(decorator)


def test_load_rbac_contract_unchanged(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.valid is True
    assert result.exists is False
