"""Garde-fou ENTITY-CONTRACT-015.

Vérifie que forge make:relation génère des relations many_to_one canoniques
(schema_version: "1.0") conformes à schemas/relations.schema.json,
sans clés legacy (from_entity, to_entity, foreign_key_name, etc.).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from forge_cli.entities import make_relation
from forge_cli.entities.make_entity import main as make_entity_main


PROJECT_ROOT = Path(__file__).parent.parent


# ── Fixtures communes ─────────────────────────────────────────────────────────

def _legacy_entity(name: str, table: str, extra_fields: list[dict] | None = None) -> dict:
    fields = [{"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True}]
    fields.extend(extra_fields or [])
    return {"entity": name, "fields": fields}


def _write_entity(entities_dir: Path, folder: str, data: dict) -> None:
    d = entities_dir / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / f"{folder}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _setup_two_entities(tmp_path: Path) -> Path:
    entities_dir = tmp_path / "mvc" / "entities"
    _write_entity(entities_dir, "article", _legacy_entity("Article", "article"))
    _write_entity(entities_dir, "category", _legacy_entity("Category", "category"))
    return entities_dir


def _run_make_relation(monkeypatch, tmp_path: Path, answers: list[str]) -> dict:
    """Lance make_relation et retourne le JSON écrit."""
    monkeypatch.chdir(tmp_path)
    entities_dir = tmp_path / "mvc" / "entities"
    _write_entity(entities_dir, "article", _legacy_entity("Article", "article"))
    _write_entity(entities_dir, "category", _legacy_entity("Category", "category"))
    answers_iter = iter(answers)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers_iter))
    make_relation.main([])
    return json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))


_ANSWERS_ARTICLE_CATEGORY = [
    "",          # type (many_to_one)
    "Article",   # from
    "Category",  # to
    "category",  # name
    "articles",  # inverse_name
    "",          # foreign_key (default: category_id)
    "",          # nullable (default: True)
    "",          # on_delete (default: restrict)
    "",          # index (default: True)
    "o",         # confirm
]

_ANSWERS_DEFAULTS_ONLY = [
    "",          # type
    "Article",   # from
    "Category",  # to
    "",          # name (default: category)
    "",          # inverse_name (empty)
    "",          # foreign_key (default: category_id)
    "",          # nullable (default: True)
    "",          # on_delete (default: restrict)
    "",          # index (default: True)
    "o",         # confirm
]


# ── Format racine du document ─────────────────────────────────────────────────

def test_relations_json_has_schema_version(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["schema_version"] == "1.0"


def test_relations_json_has_no_format_version(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "format_version" not in doc


def test_relations_json_has_relations_list(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert isinstance(doc["relations"], list)
    assert len(doc["relations"]) == 1


# ── Champs obligatoires de la relation ────────────────────────────────────────

def test_relation_type_is_many_to_one(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["type"] == "many_to_one"


def test_relation_has_from(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["from"] == "Article"


def test_relation_has_to(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["to"] == "Category"


def test_relation_has_name(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["name"] == "category"


# ── Champs optionnels ─────────────────────────────────────────────────────────

def test_relation_has_foreign_key(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["foreign_key"] == "category_id"


def test_relation_foreign_key_derives_from_name(monkeypatch, tmp_path):
    """foreign_key par défaut = name + '_id'."""
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    rel = doc["relations"][0]
    assert rel["foreign_key"] == f"{rel['name']}_id"


def test_relation_has_nullable_boolean(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert isinstance(doc["relations"][0]["nullable"], bool)


def test_relation_nullable_default_true(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["nullable"] is True


def test_relation_has_on_delete_lowercase(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    on_delete = doc["relations"][0]["on_delete"]
    assert on_delete == on_delete.lower()


def test_relation_on_delete_default_restrict(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["on_delete"] == "restrict"


def test_relation_has_index_boolean(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert isinstance(doc["relations"][0]["index"], bool)


def test_relation_index_default_true(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert doc["relations"][0]["index"] is True


def test_relation_inverse_name_included_when_provided(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_ARTICLE_CATEGORY)
    assert doc["relations"][0]["inverse_name"] == "articles"


def test_relation_inverse_name_omitted_when_empty(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "inverse_name" not in doc["relations"][0]


# ── Absence de clés legacy ────────────────────────────────────────────────────

def test_relation_no_from_entity(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "from_entity" not in doc["relations"][0]


def test_relation_no_to_entity(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "to_entity" not in doc["relations"][0]


def test_relation_no_foreign_key_name(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "foreign_key_name" not in doc["relations"][0]


def test_relation_no_from_field(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "from_field" not in doc["relations"][0]


def test_relation_no_to_field(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "to_field" not in doc["relations"][0]


def test_relation_no_on_update(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    assert "on_update" not in doc["relations"][0]


def test_relations_json_no_source_target_pivot(monkeypatch, tmp_path):
    doc = _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)
    rel = doc["relations"][0]
    for key in ("source", "target", "pivot_table", "source_key", "target_key"):
        assert key not in rel


# ── Validation JSON Schema ────────────────────────────────────────────────────

def test_relations_json_validates_against_schema(monkeypatch, tmp_path):
    """Le JSON généré doit valider contre relations.schema.json."""
    pytest.importorskip("jsonschema")
    _run_make_relation(monkeypatch, tmp_path, _ANSWERS_DEFAULTS_ONLY)

    from forge_cli.entities.entity_validate import collect_entity_validation_results
    results = collect_entity_validation_results(tmp_path / "mvc" / "entities")
    assert results is not None
    assert results["errors"] == [], f"Erreurs de schema : {results['errors']}"


# ── entity:validate CLI ───────────────────────────────────────────────────────

def test_entity_validate_passes_after_make_relation(monkeypatch, tmp_path):
    """entity:validate doit retourner valid=true après make:relation."""
    pytest.importorskip("jsonschema")
    monkeypatch.chdir(tmp_path)
    entities_dir = tmp_path / "mvc" / "entities"
    _write_entity(entities_dir, "article", _legacy_entity("Article", "article"))
    _write_entity(entities_dir, "category", _legacy_entity("Category", "category"))

    # Write a valid canonical relations.json directly (simulating make:relation output)
    relations = {
        "schema_version": "1.0",
        "relations": [{
            "type": "many_to_one",
            "from": "Article",
            "to": "Category",
            "name": "category",
            "foreign_key": "category_id",
            "nullable": True,
            "on_delete": "restrict",
            "index": True,
        }],
    }
    (entities_dir / "relations.json").write_text(json.dumps(relations, indent=2) + "\n", encoding="utf-8")

    from forge_cli.entities.entity_validate import collect_entity_validation_results
    results = collect_entity_validation_results(entities_dir)
    assert results is not None
    assert results["errors"] == []


# ── build:model ne plante pas ─────────────────────────────────────────────────

def test_build_model_does_not_crash_with_canonical_relations(monkeypatch, tmp_path):
    """build:model ne doit pas planter avec un relations.json canonique."""
    monkeypatch.chdir(tmp_path)

    # Create canonical entities
    make_entity_main(["Article", "--no-input"])
    make_entity_main(["Category", "--no-input"])

    # Overwrite relations.json with a canonical many_to_one
    entities_dir = tmp_path / "mvc" / "entities"
    relations = {
        "schema_version": "1.0",
        "relations": [{
            "type": "many_to_one",
            "from": "Article",
            "to": "Category",
            "name": "category",
            "foreign_key": "category_id",
            "nullable": True,
            "on_delete": "restrict",
            "index": True,
        }],
    }
    (entities_dir / "relations.json").write_text(json.dumps(relations, indent=2) + "\n", encoding="utf-8")

    from forge_cli.entities.model import build_model
    result = build_model(entities_dir)
    assert result is not None


# ── make:entity initialise relations.json canonique ──────────────────────────

def test_make_entity_writes_canonical_relations_json(monkeypatch, tmp_path):
    """make:entity doit initialiser relations.json au format canonique."""
    monkeypatch.chdir(tmp_path)
    make_entity_main(["Article", "--no-input"])

    entities_dir = tmp_path / "mvc" / "entities"
    data = json.loads((entities_dir / "relations.json").read_text(encoding="utf-8"))
    assert data["schema_version"] == "1.0"
    assert "format_version" not in data
    assert data["relations"] == []


# ── entity:validate --json — format de sortie inchangé ───────────────────────

def test_entity_validate_json_output_unchanged_after_015():
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
