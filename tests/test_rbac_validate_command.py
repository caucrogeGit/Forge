"""Tests — RBAC-CONTRACT-003 : commande forge rbac:validate.

Vérifie le comportement de rbac:validate :
- fichier absent → valid true, exists false, exit 0
- fichier valide → valid true, exit 0
- fichier invalide → valid false, exit 1
- sortie --json correcte
- option inconnue → exit 1
"""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch

from forge_mvc_rbac.cli.rbac_validate import rbac_validate_main

PROJECT_ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str], *, cwd: Path | None = None) -> tuple[str, str, int]:
    """Exécute rbac_validate_main et retourne (stdout, stderr, exit_code)."""
    out = StringIO()
    err = StringIO()
    code = 0
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            if cwd is not None:
                with patch("forge_mvc_rbac.cli.rbac_validate.Path.cwd", return_value=cwd):
                    rbac_validate_main(args)
            else:
                rbac_validate_main(args)
        except SystemExit as exc:
            code = int(exc.code) if exc.code is not None else 0
    return out.getvalue(), err.getvalue(), code


def _run_in(tmp_path: Path, args: list[str]) -> tuple[str, str, int]:
    """Exécute la commande avec tmp_path comme répertoire courant."""
    out = StringIO()
    err = StringIO()
    code = 0
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            with patch("forge_mvc_rbac.cli.rbac_validate.Path.cwd", return_value=tmp_path):
                rbac_validate_main(args)
        except SystemExit as exc:
            code = int(exc.code) if exc.code is not None else 0
    return out.getvalue(), err.getvalue(), code


def _write_rbac(tmp_path: Path, data: dict) -> None:
    rbac_dir = tmp_path / "mvc" / "security"
    rbac_dir.mkdir(parents=True)
    (rbac_dir / "rbac.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


_VALID_MINIMAL = {"schema_version": "1.0"}

_VALID_FULL = {
    "schema_version": "1.0",
    "entities": {
        "Article": {
            "permissions": {
                "list": "article.list",
                "create": "article.create",
            }
        }
    },
    "roles": {
        "admin": ["article.list", "article.create"],
        "reader": ["article.list"],
    },
}


# ── Import ────────────────────────────────────────────────────────────────────


def test_module_importable():
    from forge_mvc_rbac.cli import rbac_validate  # noqa: F401


def test_rbac_validate_main_callable():
    assert callable(rbac_validate_main)


# ── Fichier absent ────────────────────────────────────────────────────────────


class TestFichierAbsent:
    def test_exit_0_si_fichier_absent(self, tmp_path):
        _, _, code = _run_in(tmp_path, [])
        assert code == 0

    def test_sortie_humaine_mentionne_path(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, [])
        assert "mvc/security/rbac.json" in stdout

    def test_json_valid_true_si_fichier_absent(self, tmp_path):
        stdout, _, code = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["valid"] is True
        assert code == 0

    def test_json_exists_false_si_fichier_absent(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["exists"] is False

    def test_json_errors_vides_si_fichier_absent(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["errors_count"] == 0
        assert obj["errors"] == []

    def test_json_path_correct(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert "mvc/security/rbac.json" in obj["path"]


# ── Fichier valide ────────────────────────────────────────────────────────────


class TestFichierValide:
    def test_exit_0_si_fichier_valide(self, tmp_path):
        _write_rbac(tmp_path, _VALID_MINIMAL)
        _, _, code = _run_in(tmp_path, [])
        assert code == 0

    def test_json_valid_true(self, tmp_path):
        _write_rbac(tmp_path, _VALID_MINIMAL)
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["valid"] is True

    def test_json_exists_true(self, tmp_path):
        _write_rbac(tmp_path, _VALID_MINIMAL)
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["exists"] is True

    def test_json_errors_vides(self, tmp_path):
        _write_rbac(tmp_path, _VALID_MINIMAL)
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["errors_count"] == 0
        assert obj["errors"] == []

    def test_roles_count_correct(self, tmp_path):
        _write_rbac(tmp_path, _VALID_FULL)
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["roles_count"] == 2

    def test_entities_count_correct(self, tmp_path):
        _write_rbac(tmp_path, _VALID_FULL)
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["entities_count"] == 1

    def test_json_schema_field_present(self, tmp_path):
        _write_rbac(tmp_path, _VALID_MINIMAL)
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert "schema" in obj
        assert "rbac.schema.json" in obj["schema"]


# ── Fichier invalide ──────────────────────────────────────────────────────────


class TestFichierInvalide:
    def test_schema_version_absent_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"roles": {"admin": ["x.list"]}})
        _, _, code = _run_in(tmp_path, [])
        assert code == 1

    def test_schema_version_incorrect_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"schema_version": "2.0"})
        _, _, code = _run_in(tmp_path, [])
        assert code == 1

    def test_propriete_racine_inconnue_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"schema_version": "1.0", "cle_inconnue": "val"})
        _, _, code = _run_in(tmp_path, [])
        assert code == 1

    def test_role_non_tableau_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"schema_version": "1.0", "roles": {"admin": "admin"}})
        _, _, code = _run_in(tmp_path, [])
        assert code == 1

    def test_permission_non_string_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"schema_version": "1.0", "roles": {"admin": [42]}})
        _, _, code = _run_in(tmp_path, [])
        assert code == 1

    def test_json_valid_false_si_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"schema_version": "1.0", "cle_inconnue": "val"})
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["valid"] is False

    def test_json_errors_non_vides_si_invalide(self, tmp_path):
        _write_rbac(tmp_path, {"schema_version": "1.0", "cle_inconnue": "val"})
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert obj["errors_count"] > 0
        assert len(obj["errors"]) > 0


# ── Sortie --json ─────────────────────────────────────────────────────────────


class TestSortieJson:
    def test_json_est_json_valide(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert isinstance(obj, dict)

    def test_json_contient_valid(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert "valid" in obj

    def test_json_contient_exists(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert "exists" in obj

    def test_json_contient_errors(self, tmp_path):
        stdout, _, _ = _run_in(tmp_path, ["--json"])
        obj = json.loads(stdout)
        assert "errors" in obj
        assert "errors_count" in obj


# ── Option inconnue ───────────────────────────────────────────────────────────


def test_option_inconnue_exit_1(tmp_path):
    _, _, code = _run_in(tmp_path, ["--unknown-flag"])
    assert code == 1


def test_option_inconnue_json_valid_false(tmp_path):
    stdout, _, _ = _run_in(tmp_path, ["--json", "--unknown-flag"])
    obj = json.loads(stdout)
    assert obj["valid"] is False


# ── Aide CLI ─────────────────────────────────────────────────────────────────


def test_aide_mentionne_rbac_validate():
    from cli._support.help import build_help
    aide = build_help("test")
    assert "rbac:validate" in aide


# ── Garde-fous sur entity.schema.json et fichier utilisateur ─────────────────


def test_ne_modifie_pas_entity_schema(tmp_path):
    entity_schema = PROJECT_ROOT / "schemas" / "entity.schema.json"
    content_before = entity_schema.read_text(encoding="utf-8")
    _run_in(tmp_path, [])
    content_after = entity_schema.read_text(encoding="utf-8")
    assert content_before == content_after


def test_ne_cree_pas_rbac_json_automatiquement(tmp_path):
    _run_in(tmp_path, [])
    assert not (tmp_path / "mvc" / "security" / "rbac.json").exists()


# ── Dispatch forge.py ─────────────────────────────────────────────────────────


def test_forge_py_dispatche_rbac_validate(tmp_path, capsys):
    import forge
    with patch("sys.argv", ["forge", "rbac:validate"]), \
         patch("forge_mvc_rbac.cli.rbac_validate.Path.cwd", return_value=tmp_path):
        try:
            forge.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "mvc/security/rbac.json" in captured.out or "RBAC" in captured.out or "rbac" in captured.out.lower()
