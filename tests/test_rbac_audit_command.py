"""Tests — RBAC-MODULE-006 : commande forge rbac:audit.

Vérifie rbac_audit_main : contrat absent, invalide, valide sans avertissements,
et les sept codes d'avertissement de cohérence fonctionnelle.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.rbac_audit import rbac_audit_main


def _write_rbac(tmp_path: Path, content: dict) -> None:
    d = tmp_path / "mvc" / "security"
    d.mkdir(parents=True)
    (d / "rbac.json").write_text(json.dumps(content), encoding="utf-8")


_VALID_CONTRACT = {
    "schema_version": "1.0",
    "entities": {
        "Article": {
            "permissions": {
                "list": "article.list",
                "show": "article.show",
                "create": "article.create",
                "update": "article.update",
                "delete": "article.delete",
            }
        }
    },
    "roles": {
        "admin": ["article.list", "article.show", "article.create", "article.update", "article.delete"],
        "reader": ["article.list", "article.show"],
    },
}


# ---------------------------------------------------------------------------
# Aide
# ---------------------------------------------------------------------------


def test_rbac_audit_in_help():
    from forge_cli.help import build_help
    assert "rbac:audit" in build_help("1.0.0b5")


# ---------------------------------------------------------------------------
# Contrat absent
# ---------------------------------------------------------------------------


def test_absent_exits_0(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        rbac_audit_main([])
    assert exc.value.code == 0


def test_absent_json_valid_true(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["exists"] is False


def test_absent_json_warnings_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert result["warnings_count"] == 0
    assert result["warnings"] == []


def test_absent_json_errors_empty(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert result["errors_count"] == 0
    assert result["errors"] == []


# ---------------------------------------------------------------------------
# Contrat invalide
# ---------------------------------------------------------------------------


def test_invalid_schema_exits_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, {"schema_version": "2.0"})
    with pytest.raises(SystemExit) as exc:
        rbac_audit_main([])
    assert exc.value.code == 1


def test_invalid_json_exits_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "mvc" / "security"
    d.mkdir(parents=True)
    (d / "rbac.json").write_text("{ not valid json }", encoding="utf-8")
    with pytest.raises(SystemExit) as exc:
        rbac_audit_main([])
    assert exc.value.code == 1


def test_invalid_json_json_mode(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    d = tmp_path / "mvc" / "security"
    d.mkdir(parents=True)
    (d / "rbac.json").write_text("{ not valid json }", encoding="utf-8")
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is False
    assert result["exists"] is True


# ---------------------------------------------------------------------------
# Contrat valide sans avertissements
# ---------------------------------------------------------------------------


def test_valid_no_warnings_exits_0(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, _VALID_CONTRACT)
    with pytest.raises(SystemExit) as exc:
        rbac_audit_main([])
    assert exc.value.code == 0


def test_valid_json_no_warnings(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, _VALID_CONTRACT)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert result["valid"] is True
    assert result["exists"] is True
    assert result["warnings_count"] == 0
    assert result["warnings"] == []


def test_valid_json_counts(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, _VALID_CONTRACT)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert result["roles_count"] == 2
    assert result["entities_count"] == 1
    assert result["errors_count"] == 0


# ---------------------------------------------------------------------------
# Avertissement : empty_role
# ---------------------------------------------------------------------------


def test_empty_role_warning_code(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, {"schema_version": "1.0", "roles": {"guest": []}})
    with pytest.raises(SystemExit) as exc:
        rbac_audit_main(["--json"])
    assert exc.value.code == 0
    result = json.loads(capsys.readouterr().out)
    codes = [w["code"] for w in result["warnings"]]
    assert "empty_role" in codes


def test_empty_role_warning_names_role(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, {"schema_version": "1.0", "roles": {"guest": []}})
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    empty = [w for w in result["warnings"] if w["code"] == "empty_role"]
    assert any(w.get("role") == "guest" for w in empty)


# ---------------------------------------------------------------------------
# Avertissement : missing_roles / missing_entities
# ---------------------------------------------------------------------------


def test_missing_roles_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, {"schema_version": "1.0"})
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert "missing_roles" in [w["code"] for w in result["warnings"]]


def test_missing_entities_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, {"schema_version": "1.0", "roles": {"admin": ["a.b"]}})
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert "missing_entities" in [w["code"] for w in result["warnings"]]


# ---------------------------------------------------------------------------
# Avertissement : missing_crud_action
# ---------------------------------------------------------------------------


def test_missing_crud_action_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    contract = {
        "schema_version": "1.0",
        "entities": {
            "Article": {
                "permissions": {"list": "article.list"}
            }
        },
        "roles": {"admin": ["article.list"]},
    }
    _write_rbac(tmp_path, contract)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    codes = [w["code"] for w in result["warnings"]]
    assert "missing_crud_action" in codes


def test_missing_crud_action_identifies_action(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    contract = {
        "schema_version": "1.0",
        "entities": {
            "Article": {
                "permissions": {"list": "article.list"}
            }
        },
        "roles": {"admin": ["article.list"]},
    }
    _write_rbac(tmp_path, contract)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    crud_warnings = [w for w in result["warnings"] if w["code"] == "missing_crud_action"]
    missing_actions = {w["action"] for w in crud_warnings}
    assert {"show", "create", "update", "delete"} <= missing_actions


# ---------------------------------------------------------------------------
# Avertissement : entity_permission_unused
# ---------------------------------------------------------------------------


def test_entity_permission_unused_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    contract = {
        "schema_version": "1.0",
        "entities": {
            "Article": {
                "permissions": {
                    "list": "article.list",
                    "show": "article.show",
                    "create": "article.create",
                    "update": "article.update",
                    "delete": "article.delete",
                }
            }
        },
        "roles": {"reader": ["article.list"]},
    }
    _write_rbac(tmp_path, contract)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert "entity_permission_unused" in [w["code"] for w in result["warnings"]]


# ---------------------------------------------------------------------------
# Avertissement : role_permission_not_declared
# ---------------------------------------------------------------------------


def test_role_permission_not_declared_warning(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    contract = {
        "schema_version": "1.0",
        "entities": {
            "Article": {
                "permissions": {
                    "list": "article.list",
                    "show": "article.show",
                    "create": "article.create",
                    "update": "article.update",
                    "delete": "article.delete",
                }
            }
        },
        "roles": {"admin": ["article.list", "undeclared.permission"]},
    }
    _write_rbac(tmp_path, contract)
    with pytest.raises(SystemExit):
        rbac_audit_main(["--json"])
    result = json.loads(capsys.readouterr().out)
    assert "role_permission_not_declared" in [w["code"] for w in result["warnings"]]


# ---------------------------------------------------------------------------
# Option inconnue
# ---------------------------------------------------------------------------


def test_unknown_option_exits_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc:
        rbac_audit_main(["--unknown"])
    assert exc.value.code == 1


# ---------------------------------------------------------------------------
# Lecture seule
# ---------------------------------------------------------------------------


def test_no_file_created(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_rbac(tmp_path, _VALID_CONTRACT)
    files_before = set(tmp_path.rglob("*"))
    try:
        rbac_audit_main([])
    except SystemExit:
        pass
    assert set(tmp_path.rglob("*")) == files_before
