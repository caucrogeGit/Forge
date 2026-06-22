"""Tests pour forge schema:doctor (ENTITY-CONTRACT-022).

Valide le comportement de la commande schema:doctor :
- sortie humaine (diagnostic avec statuts)
- sortie machine --json
- gestion des erreurs (registre absent/invalide, schéma manquant/invalide/$ref mort)
- non-régression schema:list et entity:validate

Les tests appellent schema_doctor_main() directement.
"""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path
from unittest.mock import patch


from cli.schemas.schema_doctor import (
    schema_doctor_main,
    _collect_local_refs,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(args: list[str]) -> tuple[str, str, int]:
    """Exécute schema_doctor_main et retourne (stdout, stderr, exit_code)."""
    out = StringIO()
    err = StringIO()
    code = 0
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            schema_doctor_main(args)
        except SystemExit as exc:
            code = int(exc.code) if exc.code is not None else 0
    return out.getvalue(), err.getvalue(), code


# ---------------------------------------------------------------------------
# Tests — existence et import
# ---------------------------------------------------------------------------


def test_module_importable():
    from cli.schemas import schema_doctor  # noqa: F401


def test_schema_doctor_main_callable():
    assert callable(schema_doctor_main)


def test_collect_local_refs_helper():
    obj = {"$ref": "common.schema.json#/$defs/x", "nested": {"$ref": "field.schema.json"}}
    refs: set[str] = set()
    _collect_local_refs(obj, refs)
    assert "common.schema.json" in refs
    assert "field.schema.json" in refs


def test_collect_local_refs_ignores_internal():
    obj = {"$ref": "#/$defs/something"}
    refs: set[str] = set()
    _collect_local_refs(obj, refs)
    assert not refs


def test_collect_local_refs_ignores_http():
    obj = {"$ref": "https://json-schema.org/draft/2020-12/schema"}
    refs: set[str] = set()
    _collect_local_refs(obj, refs)
    assert not refs


# ---------------------------------------------------------------------------
# Tests — sortie humaine (mode normal)
# ---------------------------------------------------------------------------


def test_human_output_lists_common():
    stdout, _, code = _run([])
    assert "common" in stdout
    assert code == 0


def test_human_output_lists_all_five_schemas():
    stdout, _, _ = _run([])
    for name in ("common", "field", "entity", "pivot", "relations"):
        assert name in stdout


def test_human_output_shows_ok_for_all():
    stdout, _, code = _run([])
    assert "OK" in stdout
    assert "MANQUANT" not in stdout
    assert "INVALIDE" not in stdout
    assert "ABSENT" not in stdout
    assert code == 0


def test_human_output_shows_references():
    stdout, _, _ = _run([])
    assert "Références locales" in stdout


def test_human_output_shows_result_ok():
    stdout, _, code = _run([])
    assert "Résultat : OK" in stdout
    assert "0 erreur" in stdout
    assert code == 0


def test_human_output_shows_registry_version():
    stdout, _, _ = _run([])
    assert "forge.schema.index.json" in stdout
    assert "1.0" in stdout


# ---------------------------------------------------------------------------
# Tests — sortie JSON (--json)
# ---------------------------------------------------------------------------


def test_json_output_is_valid_json():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert isinstance(obj, dict)


def test_json_output_valid_true():
    stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is True
    assert code == 0


def test_json_output_schemas_checked_six():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["schemas_checked"] == 6


def test_json_output_errors_count_zero():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["errors_count"] == 0


def test_json_output_schema_version():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["schema_version"] == "1.0"


def test_json_output_registry_field():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["registry"] == "schemas/forge.schema.index.json"


def test_json_output_all_schemas_exist_and_valid():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    for schema in obj["schemas"]:
        assert schema["exists"] is True, f"{schema['name']} absent"
        assert schema["json_valid"] is True, f"{schema['name']} JSON invalide"


def test_json_output_all_schemas_have_schema_draft():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    for schema in obj["schemas"]:
        assert schema["schema_draft"] == _DRAFT_2020_12, f"{schema['name']} mauvais draft"


def test_json_output_all_schemas_have_id():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    for schema in obj["schemas"]:
        assert schema["id"], f"{schema['name']} sans $id"
        assert schema["id"].startswith("https://forge-mvc.dev/"), f"{schema['name']} $id inattendu"


def test_json_output_references_all_exist():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    for ref in obj["references"]:
        assert ref["exists"] is True, f"$ref mort : {ref['source']} -> {ref['ref']}"


def test_json_output_no_human_text():
    """La sortie --json doit être parsable en JSON pur."""
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert isinstance(obj, dict)


def test_json_output_contains_errors_list():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert "errors" in obj
    assert obj["errors"] == []


def test_json_output_contains_warnings_list():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert "warnings" in obj


# ---------------------------------------------------------------------------
# Tests — vérifications des schémas réels
# ---------------------------------------------------------------------------


def test_all_schemas_have_draft_2020_12():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    names_with_bad_draft = [
        s["name"] for s in obj["schemas"]
        if s.get("schema_draft") != _DRAFT_2020_12
    ]
    assert not names_with_bad_draft, f"Schémas sans Draft 2020-12 : {names_with_bad_draft}"


def test_references_include_field_and_common():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    refs = {(r["source"], r["ref"]) for r in obj["references"]}
    assert any("field.schema.json" in src for src, _ in refs), "entity ou pivot devrait référencer field.schema.json"
    assert any("common.schema.json" == ref for _, ref in refs), "common.schema.json non référencé"


# ---------------------------------------------------------------------------
# Tests — gestion des erreurs
# ---------------------------------------------------------------------------


def test_missing_registry_exits_with_error(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    with patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry):
        _, stderr, code = _run([])
    assert code == 1
    assert "introuvable" in stderr.lower() or "erreur" in stderr.lower()


def test_missing_registry_json_output(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    with patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert code == 1


def test_invalid_json_registry_exits_with_error(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text("{ not valid json }", encoding="utf-8")
    with patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry):
        _, stderr, code = _run([])
    assert code == 1
    assert "invalide" in stderr.lower() or "erreur" in stderr.lower()


def test_invalid_json_registry_json_output(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text("{ not valid json }", encoding="utf-8")
    with patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert code == 1


def test_registry_without_schemas_key(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text('{"schema_version": "1.0"}', encoding="utf-8")
    with patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry):
        _, stderr, code = _run([])
    assert code == 1


def test_missing_schema_file_reports_error(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"ghost": "./ghost.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry),
        patch("cli.schemas.schema_doctor._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run([])
    assert code == 1
    assert "MANQUANT" in stdout


def test_missing_schema_file_json_output(tmp_path):
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"ghost": "./ghost.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry),
        patch("cli.schemas.schema_doctor._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert obj["schemas"][0]["exists"] is False
    assert code == 1


def test_invalid_schema_json_content(tmp_path):
    """Schéma présent mais JSON invalide → erreur."""
    fake_registry = tmp_path / "forge.schema.index.json"
    bad_schema = tmp_path / "bad.schema.json"
    bad_schema.write_text("{ not json }", encoding="utf-8")
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"bad": "./bad.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry),
        patch("cli.schemas.schema_doctor._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run([])
    assert code == 1
    assert "INVALIDE" in stdout or "invalide" in stdout.lower()


def test_missing_dollar_schema_key(tmp_path):
    """Schéma sans $schema → erreur signalée."""
    fake_registry = tmp_path / "forge.schema.index.json"
    schema_file = tmp_path / "no_meta.schema.json"
    schema_file.write_text(
        json.dumps({"$id": "https://example.com/no_meta", "type": "object"}),
        encoding="utf-8",
    )
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"no_meta": "./no_meta.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry),
        patch("cli.schemas.schema_doctor._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run([])
    assert code == 1
    assert "$schema" in stdout or "ABSENT" in stdout


def test_dead_local_ref(tmp_path):
    """$ref local vers un fichier inexistant → erreur."""
    fake_registry = tmp_path / "forge.schema.index.json"
    schema_file = tmp_path / "with_ref.schema.json"
    schema_file.write_text(
        json.dumps({
            "$schema": _DRAFT_2020_12,
            "$id": "https://example.com/with_ref",
            "properties": {"x": {"$ref": "ghost.schema.json#/$defs/x"}},
        }),
        encoding="utf-8",
    )
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"with_ref": "./with_ref.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry),
        patch("cli.schemas.schema_doctor._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run([])
    assert code == 1
    assert "MANQUANT" in stdout


def test_dead_local_ref_json_output(tmp_path):
    """$ref mort + --json → exists=false dans references[]."""
    fake_registry = tmp_path / "forge.schema.index.json"
    schema_file = tmp_path / "with_ref.schema.json"
    schema_file.write_text(
        json.dumps({
            "$schema": _DRAFT_2020_12,
            "$id": "https://example.com/with_ref",
            "properties": {"x": {"$ref": "ghost.schema.json"}},
        }),
        encoding="utf-8",
    )
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"with_ref": "./with_ref.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("cli.schemas.schema_doctor._registry_path", return_value=fake_registry),
        patch("cli.schemas.schema_doctor._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert any(r["ref"] == "ghost.schema.json" and not r["exists"] for r in obj["references"])
    assert code == 1


def test_unknown_option_exits_with_error():
    _, stderr, code = _run(["--unknown"])
    assert code == 1


# ---------------------------------------------------------------------------
# Tests — non-régression
# ---------------------------------------------------------------------------


def test_schema_list_not_broken():
    from cli.schemas.schema_list import schema_list_main
    assert callable(schema_list_main)


def test_entity_validate_not_broken():
    from cli.entities.entity_validate import main as entity_validate_main
    assert callable(entity_validate_main)


def test_forge_py_dispatches_schema_doctor(capsys):
    """forge.py route correctement «schema:doctor» vers schema_doctor_main."""
    with patch("sys.argv", ["forge", "schema:doctor"]):
        import forge  # noqa: F401
        try:
            forge.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "schémas" in captured.out.lower() or "schemas" in captured.out.lower()


def test_help_mentions_schema_doctor():
    from cli.help import build_help
    help_text = build_help("test")
    assert "schema:doctor" in help_text
