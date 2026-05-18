"""Tests pour forge schema:list (ENTITY-CONTRACT-021).

Valide le comportement de la commande schema:list :
- sortie humaine (liste avec statuts OK / MANQUANT)
- sortie machine --json
- gestion des erreurs (registre absent, invalide, schéma manquant)
- non-régression entity:validate

Les tests appellent schema_list_main() directement afin de ne pas
dépendre du binaire global forge ni de subprocess.
"""
from __future__ import annotations

import json
import sys
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest

from forge_cli.schemas.schema_list import schema_list_main, _registry_path, _schemas_dir


PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _run(args: list[str]) -> tuple[str, str, int]:
    """Exécute schema_list_main et retourne (stdout, stderr, exit_code)."""
    out = StringIO()
    err = StringIO()
    code = 0
    with patch("sys.stdout", out), patch("sys.stderr", err):
        try:
            schema_list_main(args)
        except SystemExit as exc:
            code = int(exc.code) if exc.code is not None else 0
    return out.getvalue(), err.getvalue(), code


# ---------------------------------------------------------------------------
# Tests — existence et import
# ---------------------------------------------------------------------------


def test_module_importable():
    from forge_cli.schemas import schema_list  # noqa: F401


def test_schema_list_main_callable():
    assert callable(schema_list_main)


def test_registry_path_exists():
    assert _registry_path().exists(), "schemas/forge.schema.index.json introuvable"


def test_schemas_dir_exists():
    assert _schemas_dir().is_dir(), "dossier schemas/ introuvable"


# ---------------------------------------------------------------------------
# Tests — sortie humaine (mode normal)
# ---------------------------------------------------------------------------


def test_human_output_lists_common():
    stdout, _, code = _run([])
    assert "common" in stdout
    assert code == 0


def test_human_output_lists_field():
    stdout, _, code = _run([])
    assert "field" in stdout


def test_human_output_lists_entity():
    stdout, _, code = _run([])
    assert "entity" in stdout


def test_human_output_lists_pivot():
    stdout, _, code = _run([])
    assert "pivot" in stdout


def test_human_output_lists_relations():
    stdout, _, code = _run([])
    assert "relations" in stdout


def test_human_output_shows_ok_for_present_files():
    stdout, _, code = _run([])
    assert "OK" in stdout
    assert "MANQUANT" not in stdout
    assert code == 0


def test_human_output_shows_total():
    stdout, _, code = _run([])
    assert "Total" in stdout
    assert "5" in stdout


def test_human_output_contains_schema_paths():
    stdout, _, code = _run([])
    assert "schemas/entity.schema.json" in stdout
    assert "schemas/relations.schema.json" in stdout


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


def test_json_output_count_equals_five():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["count"] == 5


def test_json_output_schema_version():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["schema_version"] == "1.0"


def test_json_output_registry_field():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["registry"] == "schemas/forge.schema.index.json"


def test_json_output_contains_schemas_list():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert isinstance(obj["schemas"], list)
    assert len(obj["schemas"]) == 5


def test_json_output_contains_all_schema_names():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    names = {s["name"] for s in obj["schemas"]}
    assert names == {"common", "field", "entity", "pivot", "relations"}


def test_json_output_contains_paths():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    paths = {s["path"] for s in obj["schemas"]}
    assert "schemas/entity.schema.json" in paths
    assert "schemas/relations.schema.json" in paths


def test_json_output_all_schemas_exist_true():
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    for schema in obj["schemas"]:
        assert schema["exists"] is True, f"{schema['name']} signalé comme manquant"


def test_json_output_no_human_text():
    """La sortie --json ne doit contenir que du JSON pur, sans ligne humaine."""
    stdout, _, _ = _run(["--json"])
    obj = json.loads(stdout)
    assert isinstance(obj, dict)


# ---------------------------------------------------------------------------
# Tests — gestion des erreurs
# ---------------------------------------------------------------------------


def test_missing_registry_exits_with_error(tmp_path):
    """Registre absent → exit 1 avec message clair."""
    fake_registry = tmp_path / "forge.schema.index.json"
    with patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry):
        _, stderr, code = _run([])
    assert code == 1
    assert "introuvable" in stderr.lower() or "erreur" in stderr.lower()


def test_missing_registry_json_output(tmp_path):
    """Registre absent + --json → JSON avec valid=false."""
    fake_registry = tmp_path / "forge.schema.index.json"
    with patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert code == 1


def test_invalid_json_registry_exits_with_error(tmp_path):
    """Registre JSON malformé → exit 1 avec message clair."""
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text("{ not valid json }", encoding="utf-8")
    with patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry):
        _, stderr, code = _run([])
    assert code == 1
    assert "invalide" in stderr.lower() or "erreur" in stderr.lower()


def test_invalid_json_registry_json_output(tmp_path):
    """Registre JSON malformé + --json → JSON avec valid=false."""
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text("{ not valid json }", encoding="utf-8")
    with patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert code == 1


def test_registry_without_schemas_key_exits_with_error(tmp_path):
    """Registre sans clé 'schemas' → exit 1."""
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text('{"schema_version": "1.0"}', encoding="utf-8")
    with patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry):
        _, stderr, code = _run([])
    assert code == 1


def test_missing_schema_file_reports_manquant(tmp_path):
    """Schéma référencé mais absent → signalé MANQUANT, exit 1."""
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"ghost": "./ghost.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry),
        patch("forge_cli.schemas.schema_list._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run([])
    assert "MANQUANT" in stdout
    assert code == 1


def test_missing_schema_file_json_output(tmp_path):
    """Schéma absent + --json → exists=false, valid=false."""
    fake_registry = tmp_path / "forge.schema.index.json"
    fake_registry.write_text(
        json.dumps({"schema_version": "1.0", "schemas": {"ghost": "./ghost.schema.json"}}),
        encoding="utf-8",
    )
    with (
        patch("forge_cli.schemas.schema_list._registry_path", return_value=fake_registry),
        patch("forge_cli.schemas.schema_list._schemas_dir", return_value=tmp_path),
    ):
        stdout, _, code = _run(["--json"])
    obj = json.loads(stdout)
    assert obj["valid"] is False
    assert obj["schemas"][0]["exists"] is False
    assert code == 1


def test_unknown_option_exits_with_error():
    _, stderr, code = _run(["--unknown"])
    assert code == 1
    assert "inconnue" in stderr or "inconnue" in _run(["--unknown"])[0]


# ---------------------------------------------------------------------------
# Tests — non-régression entity:validate
# ---------------------------------------------------------------------------


def test_entity_validate_not_broken():
    """schema:list ne doit pas casser entity:validate."""
    from forge_cli.entities.entity_validate import main as entity_validate_main
    assert callable(entity_validate_main)


def test_entity_validate_still_runs(tmp_path):
    """entity:validate sur un projet vide doit terminer sans lever d'exception inattendue."""
    from forge_cli.entities.entity_validate import main as entity_validate_main
    entities_dir = tmp_path / "mvc" / "entities"
    entities_dir.mkdir(parents=True)
    out = StringIO()
    with patch("sys.stdout", out):
        try:
            entity_validate_main([])
        except SystemExit:
            pass


# ---------------------------------------------------------------------------
# Tests — intégration forge.py dispatch
# ---------------------------------------------------------------------------


def test_forge_py_dispatches_schema_list(capsys):
    """forge.py route correctement «schema:list» vers schema_list_main."""
    with patch("sys.argv", ["forge", "schema:list"]):
        import importlib
        import forge  # noqa: F401
        try:
            forge.main()
        except SystemExit:
            pass
    captured = capsys.readouterr()
    assert "schémas" in captured.out.lower() or "schemas" in captured.out.lower()


def test_help_mentions_schema_list():
    """L'aide générale mentionne schema:list."""
    from forge_cli.help import build_help
    help_text = build_help("test")
    assert "schema:list" in help_text
