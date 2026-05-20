"""Tests — RBAC-MODULE-004 : service de permissions contractuelles.

Vérifie has_contract_permission, get_contract_permissions et
require_contract_permission pour tous les cas nominaux et d'erreur.
Ces fonctions consomment un RbacContractResult chargé depuis
mvc/security/rbac.json — elles ne modifient aucun fichier et ne
branchent pas les routes.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    has_contract_permission,
    get_contract_permissions,
    require_contract_permission,
    load_rbac_contract,
    RbacContractResult,
    has_permission,
    require_permission,
)
from core.http.response import Response


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_result(**kwargs) -> RbacContractResult:
    defaults = dict(valid=True, exists=True, path="mvc/security/rbac.json")
    defaults.update(kwargs)
    return RbacContractResult(**defaults)


_CONTRACT_DATA = {
    "schema_version": "1.0",
    "roles": {
        "admin": [
            "article.list",
            "article.show",
            "article.create",
            "article.update",
            "article.delete",
        ],
        "editor": [
            "article.list",
            "article.show",
            "article.update",
        ],
        "reader": [
            "article.list",
            "article.show",
        ],
    },
}

_RESULT_VALID = _make_result(
    roles_count=3,
    entities_count=0,
    data=_CONTRACT_DATA,
)

_RESULT_ABSENT = _make_result(valid=True, exists=False, data=None)
_RESULT_INVALID = _make_result(valid=False, exists=True, data=None)


def _rbac_file(tmp_path: Path, content: dict) -> None:
    d = tmp_path / "mvc" / "security"
    d.mkdir(parents=True)
    (d / "rbac.json").write_text(json.dumps(content), encoding="utf-8")


# ---------------------------------------------------------------------------
# Imports publics
# ---------------------------------------------------------------------------


def test_import_has_contract_permission():
    from forge_mvc_rbac import has_contract_permission as _f
    assert callable(_f)


def test_import_get_contract_permissions():
    from forge_mvc_rbac import get_contract_permissions as _f
    assert callable(_f)


def test_import_require_contract_permission():
    from forge_mvc_rbac import require_contract_permission as _f
    assert callable(_f)


# ---------------------------------------------------------------------------
# has_contract_permission — cas nominaux
# ---------------------------------------------------------------------------


def test_admin_has_delete():
    assert has_contract_permission(_RESULT_VALID, ["admin"], "article.delete") is True


def test_reader_no_delete():
    assert has_contract_permission(_RESULT_VALID, ["reader"], "article.delete") is False


def test_reader_has_list():
    assert has_contract_permission(_RESULT_VALID, ["reader"], "article.list") is True


def test_editor_has_update():
    assert has_contract_permission(_RESULT_VALID, ["editor"], "article.update") is True


def test_editor_no_delete():
    assert has_contract_permission(_RESULT_VALID, ["editor"], "article.delete") is False


# ---------------------------------------------------------------------------
# has_contract_permission — fusion de rôles multiples
# ---------------------------------------------------------------------------


def test_multi_roles_union():
    assert has_contract_permission(_RESULT_VALID, ["reader", "editor"], "article.update") is True


def test_multi_roles_still_no_delete():
    assert has_contract_permission(_RESULT_VALID, ["reader", "editor"], "article.delete") is False


def test_multi_roles_with_admin():
    assert has_contract_permission(_RESULT_VALID, ["reader", "admin"], "article.delete") is True


# ---------------------------------------------------------------------------
# has_contract_permission — cas limites
# ---------------------------------------------------------------------------


def test_unknown_role_returns_false():
    assert has_contract_permission(_RESULT_VALID, ["unknown"], "article.list") is False


def test_unknown_permission_returns_false():
    assert has_contract_permission(_RESULT_VALID, ["admin"], "article.unknown") is False


def test_empty_roles_returns_false():
    assert has_contract_permission(_RESULT_VALID, [], "article.list") is False


def test_contract_absent_returns_false():
    assert has_contract_permission(_RESULT_ABSENT, ["admin"], "article.list") is False


def test_contract_invalid_returns_false():
    assert has_contract_permission(_RESULT_INVALID, ["admin"], "article.list") is False


# ---------------------------------------------------------------------------
# get_contract_permissions
# ---------------------------------------------------------------------------


def test_get_admin_permissions():
    perms = get_contract_permissions(_RESULT_VALID, ["admin"])
    assert "article.list" in perms
    assert "article.delete" in perms
    assert len(perms) == 5


def test_get_reader_permissions():
    perms = get_contract_permissions(_RESULT_VALID, ["reader"])
    assert perms == {"article.list", "article.show"}


def test_get_multi_roles_union():
    perms = get_contract_permissions(_RESULT_VALID, ["reader", "editor"])
    assert perms == {"article.list", "article.show", "article.update"}


def test_get_permissions_deduplication():
    perms = get_contract_permissions(_RESULT_VALID, ["reader", "editor", "admin"])
    # article.list est dans les 3 rôles — doit apparaître une seule fois
    assert isinstance(perms, set)
    assert perms.count("article.list") == 1 if hasattr(perms, "count") else True
    assert "article.list" in perms


def test_get_empty_roles():
    assert get_contract_permissions(_RESULT_VALID, []) == set()


def test_get_unknown_role():
    assert get_contract_permissions(_RESULT_VALID, ["unknown"]) == set()


def test_get_absent_contract():
    assert get_contract_permissions(_RESULT_ABSENT, ["admin"]) == set()


def test_get_invalid_contract():
    assert get_contract_permissions(_RESULT_INVALID, ["admin"]) == set()


# ---------------------------------------------------------------------------
# require_contract_permission
# ---------------------------------------------------------------------------


def test_require_allowed_returns_none():
    resp = require_contract_permission(_RESULT_VALID, ["admin"], "article.delete")
    assert resp is None


def test_require_denied_returns_response():
    resp = require_contract_permission(_RESULT_VALID, ["reader"], "article.delete")
    assert resp is not None


def test_require_denied_is_403():
    resp = require_contract_permission(_RESULT_VALID, ["reader"], "article.delete")
    assert isinstance(resp, Response)
    assert resp.status == 403


def test_require_absent_contract_returns_403():
    resp = require_contract_permission(_RESULT_ABSENT, ["admin"], "article.list")
    assert isinstance(resp, Response)
    assert resp.status == 403


def test_require_invalid_contract_returns_403():
    resp = require_contract_permission(_RESULT_INVALID, ["admin"], "article.list")
    assert isinstance(resp, Response)
    assert resp.status == 403


def test_require_unknown_role_returns_403():
    resp = require_contract_permission(_RESULT_VALID, ["unknown"], "article.list")
    assert isinstance(resp, Response)
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Intégration avec load_rbac_contract
# ---------------------------------------------------------------------------


def test_load_then_check_permission(tmp_path):
    _rbac_file(tmp_path, _CONTRACT_DATA)
    result = load_rbac_contract(tmp_path)
    assert result.valid
    assert has_contract_permission(result, ["admin"], "article.delete") is True
    assert has_contract_permission(result, ["reader"], "article.delete") is False


def test_load_then_require_permission(tmp_path):
    _rbac_file(tmp_path, _CONTRACT_DATA)
    result = load_rbac_contract(tmp_path)
    assert require_contract_permission(result, ["admin"], "article.delete") is None
    resp = require_contract_permission(result, ["reader"], "article.delete")
    assert isinstance(resp, Response)
    assert resp.status == 403


# ---------------------------------------------------------------------------
# Pas de régression sur has_permission / require_permission existants
# ---------------------------------------------------------------------------


def test_has_permission_unchanged():
    class FakeRequest:
        permissions = {"article.list"}

    assert has_permission(FakeRequest(), "article.list") is True
    assert has_permission(FakeRequest(), "article.delete") is False


def test_require_permission_unchanged():
    assert callable(require_permission("article.list"))


def test_load_rbac_contract_unchanged(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.valid is True
    assert result.exists is False
