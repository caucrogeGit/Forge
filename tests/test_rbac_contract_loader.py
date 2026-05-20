"""Tests — RBAC-MODULE-003 : chargeur du contrat mvc/security/rbac.json.

Vérifie le comportement de load_rbac_contract() pour tous les cas nominaux
et d'erreur. Ce chargeur est lecture seule — il ne crée ni ne modifie
aucun fichier.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import load_rbac_contract, RbacContractResult, RbacContractError
from forge_mvc_rbac.rbac import has_permission, require_permission


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rbac_dir(tmp_path: Path) -> Path:
    d = tmp_path / "mvc" / "security"
    d.mkdir(parents=True)
    return d


def _write_rbac(tmp_path: Path, content: dict | str) -> Path:
    d = _rbac_dir(tmp_path)
    path = d / "rbac.json"
    if isinstance(content, dict):
        path.write_text(json.dumps(content), encoding="utf-8")
    else:
        path.write_text(content, encoding="utf-8")
    return path


_VALID_MINIMAL = {"schema_version": "1.0"}

_VALID_WITH_ROLES = {
    "schema_version": "1.0",
    "roles": {
        "admin": ["article.list", "article.show"],
        "editor": ["article.list"],
    },
}

_VALID_WITH_ENTITIES = {
    "schema_version": "1.0",
    "entities": {
        "Article": {
            "permissions": {
                "list": "article.list",
                "show": "article.show",
            }
        },
        "Tag": {
            "permissions": {
                "list": "tag.list",
            }
        },
    },
}

_VALID_FULL = {
    "schema_version": "1.0",
    "roles": {
        "admin": ["article.list"],
    },
    "entities": {
        "Article": {
            "permissions": {
                "list": "article.list",
            }
        },
    },
}


# ---------------------------------------------------------------------------
# Import public
# ---------------------------------------------------------------------------


def test_import_load_rbac_contract():
    from forge_mvc_rbac import load_rbac_contract as _f
    assert callable(_f)


def test_import_rbac_contract_result():
    from forge_mvc_rbac import RbacContractResult as _cls
    assert _cls is RbacContractResult


def test_import_rbac_contract_error():
    from forge_mvc_rbac import RbacContractError as _cls
    assert _cls is RbacContractError


# ---------------------------------------------------------------------------
# Fichier absent
# ---------------------------------------------------------------------------


def test_absent_valid_true(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.valid is True


def test_absent_exists_false(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.exists is False


def test_absent_no_errors(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.errors == []


def test_absent_counts_zero(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.roles_count == 0
    assert result.entities_count == 0


def test_absent_data_none(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert result.data is None


# ---------------------------------------------------------------------------
# Fichier valide minimal
# ---------------------------------------------------------------------------


def test_valid_minimal_valid_true(tmp_path):
    _write_rbac(tmp_path, _VALID_MINIMAL)
    result = load_rbac_contract(tmp_path)
    assert result.valid is True


def test_valid_minimal_exists_true(tmp_path):
    _write_rbac(tmp_path, _VALID_MINIMAL)
    result = load_rbac_contract(tmp_path)
    assert result.exists is True


def test_valid_minimal_no_errors(tmp_path):
    _write_rbac(tmp_path, _VALID_MINIMAL)
    result = load_rbac_contract(tmp_path)
    assert result.errors == []


def test_valid_minimal_data_present(tmp_path):
    _write_rbac(tmp_path, _VALID_MINIMAL)
    result = load_rbac_contract(tmp_path)
    assert result.data is not None
    assert result.data.get("schema_version") == "1.0"


# ---------------------------------------------------------------------------
# Compteurs roles et entities
# ---------------------------------------------------------------------------


def test_valid_roles_count(tmp_path):
    _write_rbac(tmp_path, _VALID_WITH_ROLES)
    result = load_rbac_contract(tmp_path)
    assert result.valid is True
    assert result.roles_count == 2


def test_valid_entities_count(tmp_path):
    _write_rbac(tmp_path, _VALID_WITH_ENTITIES)
    result = load_rbac_contract(tmp_path)
    assert result.valid is True
    assert result.entities_count == 2


def test_valid_full_counts(tmp_path):
    _write_rbac(tmp_path, _VALID_FULL)
    result = load_rbac_contract(tmp_path)
    assert result.valid is True
    assert result.roles_count == 1
    assert result.entities_count == 1


# ---------------------------------------------------------------------------
# Fichier invalide — schema_version
# ---------------------------------------------------------------------------


def test_invalid_schema_version_absent(tmp_path):
    _write_rbac(tmp_path, {})
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.exists is True
    assert result.errors


def test_invalid_schema_version_wrong(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "2.0"})
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.errors


# ---------------------------------------------------------------------------
# Fichier invalide — structure roles/entities
# ---------------------------------------------------------------------------


def test_invalid_roles_not_object(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "1.0", "roles": ["admin"]})
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.errors


def test_invalid_role_not_array(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "1.0", "roles": {"admin": "article.list"}})
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.errors


def test_invalid_permission_not_string(tmp_path):
    _write_rbac(tmp_path, {
        "schema_version": "1.0",
        "roles": {"admin": [42]},
    })
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.errors


def test_invalid_unknown_root_property(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "1.0", "unknown_key": "value"})
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.errors


# ---------------------------------------------------------------------------
# JSON invalide
# ---------------------------------------------------------------------------


def test_invalid_json_valid_false(tmp_path):
    _write_rbac(tmp_path, "{invalid json}")
    result = load_rbac_contract(tmp_path)
    assert result.valid is False
    assert result.exists is True


def test_invalid_json_has_error(tmp_path):
    _write_rbac(tmp_path, "{invalid json}")
    result = load_rbac_contract(tmp_path)
    assert result.errors
    assert result.errors[0].path == "$"


def test_invalid_json_no_exception_raised(tmp_path):
    _write_rbac(tmp_path, "{invalid json}")
    result = load_rbac_contract(tmp_path)
    assert isinstance(result, RbacContractResult)


# ---------------------------------------------------------------------------
# Lecture seule — aucun fichier créé
# ---------------------------------------------------------------------------


def test_no_file_created_when_absent(tmp_path):
    files_before = list(tmp_path.rglob("*"))
    load_rbac_contract(tmp_path)
    files_after = list(tmp_path.rglob("*"))
    assert files_before == files_after


def test_no_file_created_when_invalid(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "2.0"})
    files_before = sorted(str(f) for f in tmp_path.rglob("*"))
    load_rbac_contract(tmp_path)
    files_after = sorted(str(f) for f in tmp_path.rglob("*"))
    assert files_before == files_after


# ---------------------------------------------------------------------------
# has_permission / require_permission inchangés
# ---------------------------------------------------------------------------


def test_has_permission_not_affected(tmp_path):
    _write_rbac(tmp_path, _VALID_FULL)
    load_rbac_contract(tmp_path)

    class FakeRequest:
        permissions = {"article.list"}

    assert has_permission(FakeRequest(), "article.list") is True
    assert has_permission(FakeRequest(), "article.delete") is False


def test_require_permission_not_affected(tmp_path):
    _write_rbac(tmp_path, _VALID_FULL)
    load_rbac_contract(tmp_path)
    assert callable(require_permission("article.list"))


# ---------------------------------------------------------------------------
# Type de retour
# ---------------------------------------------------------------------------


def test_result_is_rbac_contract_result(tmp_path):
    result = load_rbac_contract(tmp_path)
    assert isinstance(result, RbacContractResult)


def test_error_is_rbac_contract_error(tmp_path):
    _write_rbac(tmp_path, {"schema_version": "2.0"})
    result = load_rbac_contract(tmp_path)
    assert all(isinstance(e, RbacContractError) for e in result.errors)
