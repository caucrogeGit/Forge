"""Garde-fou ENTITY-CONTRACT-014.

Vérifie que forge make:entity génère des contrats canoniques (schema_version: "1.0")
conformes à entity.schema.json, sans aucun champ legacy (sql_type, entity, primary_key, etc.).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from forge_mvc_entities import make_entity
from forge_mvc_entities.make_entity import build_entity_json_canonical


PROJECT_ROOT = Path(__file__).parent.parent


# ── build_entity_json_canonical — format de base ─────────────────────────────

def test_canonical_has_schema_version():
    result = build_entity_json_canonical("Article")
    assert result["schema_version"] == "1.0"


def test_canonical_has_name_not_entity():
    result = build_entity_json_canonical("Article")
    assert result["name"] == "Article"
    assert "entity" not in result


def test_canonical_derives_table_from_name():
    result = build_entity_json_canonical("UserProfile")
    assert result["table"] == "user_profile"


def test_canonical_accepts_explicit_table():
    result = build_entity_json_canonical("Article", table="blog_articles")
    assert result["table"] == "blog_articles"


def test_canonical_has_no_id_field():
    result = build_entity_json_canonical("Article")
    names = [f["name"] for f in result["fields"]]
    assert "id" not in names


def test_canonical_fields_not_empty():
    result = build_entity_json_canonical("Article")
    assert len(result["fields"]) >= 1


def test_canonical_placeholder_field_type_is_forge_type():
    result = build_entity_json_canonical("Article")
    from forge_mvc_entities.make_entity import FORGE_TYPES
    assert result["fields"][0]["type"] in FORGE_TYPES


def test_canonical_has_options():
    result = build_entity_json_canonical("Article")
    assert "options" in result
    assert result["options"]["timestamps"] is False
    assert result["options"]["soft_delete"] is False


def test_canonical_no_legacy_keys():
    result = build_entity_json_canonical("Article")
    legacy_keys = {"format_version", "sql_type", "python_type", "primary_key", "auto_increment", "column", "constraints"}
    for field in result["fields"]:
        assert not legacy_keys.intersection(field.keys()), f"Champs legacy trouvés dans {field}"
    assert "format_version" not in result
    assert "entity" not in result


# ── forge make:entity --no-input — intégration ───────────────────────────────

def test_no_input_generates_canonical_json(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    make_entity.main(["Article", "--no-input"])
    data = json.loads((tmp_path / "mvc" / "entities" / "article" / "article.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["name"] == "Article"


def test_no_input_json_validates_against_schema(monkeypatch, tmp_path):
    """Le JSON généré doit valider contre entity.schema.json."""
    pytest.importorskip("jsonschema")
    monkeypatch.chdir(tmp_path)
    make_entity.main(["Article", "--no-input"])

    from forge_mvc_entities.entity_validate import collect_entity_validation_results
    entities_root = tmp_path / "mvc" / "entities"
    results = collect_entity_validation_results(entities_root)
    assert results is not None
    assert results["errors"] == [], f"Erreurs de schema : {results['errors']}"


def test_no_input_generates_sql_file(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    make_entity.main(["Article", "--no-input"])
    sql_path = tmp_path / "mvc" / "entities" / "article" / "article.sql"
    assert sql_path.exists()
    assert "CREATE TABLE" in sql_path.read_text(encoding="utf-8")


def test_no_input_generates_base_py(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    make_entity.main(["Article", "--no-input"])
    base_path = tmp_path / "mvc" / "entities" / "article" / "article_base.py"
    assert base_path.exists()
    assert "ArticleBase" in base_path.read_text(encoding="utf-8")


# ── forge make:entity interactif — format canonique ──────────────────────────

def test_interactive_canonical_field_type_string(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    answers = iter(["", "titre", "string", "200", "", "n", "n", "n", "n", "n", "o"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Article"])

    data = json.loads((tmp_path / "mvc" / "entities" / "article" / "article.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert data["fields"][0]["type"] == "string"
    assert data["fields"][0]["max_length"] == 200


def test_interactive_canonical_options_timestamps(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    answers = iter(["", "titre", "string", "", "", "n", "n", "n", "o", "n", "o"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Article"])

    data = json.loads((tmp_path / "mvc" / "entities" / "article" / "article.json").read_text(encoding="utf-8"))
    assert data["options"]["timestamps"] is True
    assert data["options"]["soft_delete"] is False


def test_interactive_canonical_options_soft_delete(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    answers = iter(["", "titre", "string", "", "", "n", "n", "n", "n", "o", "o"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Article"])

    data = json.loads((tmp_path / "mvc" / "entities" / "article" / "article.json").read_text(encoding="utf-8"))
    assert data["options"]["soft_delete"] is True


def test_interactive_no_legacy_keys_in_output(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    answers = iter(["", "nom", "string", "100", "", "n", "n", "n", "n", "n", "o"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    make_entity.main(["Contact"])

    data = json.loads((tmp_path / "mvc" / "entities" / "contact" / "contact.json").read_text(encoding="utf-8"))
    assert "entity" not in data
    assert "format_version" not in data
    for field in data["fields"]:
        assert "sql_type" not in field
        assert "primary_key" not in field
        assert "auto_increment" not in field


# ── entity:validate — CLI — format de sortie inchangé ────────────────────────

def test_entity_validate_json_output_unchanged_after_014():
    """entity:validate --json continue à retourner le format attendu."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    for key in ("valid", "files_checked", "files_valid", "errors_count", "warnings_count", "errors", "warnings"):
        assert key in output, f"Clé manquante : {key}"


# ── Audit documentaire — fonctions supprimées ─────────────────────────────────

def test_legacy_sql_type_functions_removed():
    """Les fonctions SQL legacy ne doivent plus exister dans make_entity."""
    source = Path(make_entity.__file__).read_text(encoding="utf-8")
    assert "_is_supported_sql_type" not in source
    assert "_sql_family_for_prompt" not in source
    assert "_prompt_sql_type" not in source
    assert "_build_primary_field" not in source
    assert "_build_additional_field" not in source


def test_canonical_builder_function_exists():
    source = Path(make_entity.__file__).read_text(encoding="utf-8")
    assert "build_entity_json_canonical" in source
    assert "_build_canonical_field" in source
    assert "_prompt_forge_type" in source
