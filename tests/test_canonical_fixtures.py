"""Garde-fou ENTITY-CONTRACT-019-CANONICAL-FIXTURES.

Vérifie que les fixtures canoniques Forge sont valides, sans legacy,
et que entity:validate et build:model fonctionnent correctement sur ces fixtures.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "entities" / "canonical"

# Tous les fichiers de fixtures canoniques (tests structurels JSON)
ALL_ENTITY_NAMES = ["account", "article", "category", "member", "project", "tag"]

# Entités compatibles build_model : dossier = to_snake(entity_name), sans mot réservé SQL
BUILD_ENTITY_NAMES = ["article", "category", "tag", "member", "project"]

LEGACY_KEYS = frozenset({
    "format_version", "entity", "from_entity", "to_entity",
    "foreign_key_name", "source", "target", "pivot_table",
    "source_key", "target_key", "sql_type", "python_type",
    "primary_key", "auto_increment",
})


# ── Fixtures pytest ───────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def tmp_project(tmp_path_factory):
    """Copie les 5 fixtures buildables dans un projet temporaire mvc/entities/."""
    root = tmp_path_factory.mktemp("canonical_project")
    entities_root = root / "mvc" / "entities"
    for name in BUILD_ENTITY_NAMES:
        src = FIXTURES_DIR / name / f"{name}.json"
        dst_dir = entities_root / name
        dst_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst_dir / f"{name}.json")
    shutil.copy2(FIXTURES_DIR / "relations.json", entities_root / "relations.json")
    return entities_root


@pytest.fixture(scope="module")
def built_project(tmp_project):
    """Lance build:model une fois sur le projet temporaire et retourne entities_root."""
    from cli.entities.model import build_model
    build_model(tmp_project)
    return tmp_project


# ── Présence du dossier et des fichiers ───────────────────────────────────────

def test_fixtures_dir_exists():
    assert FIXTURES_DIR.exists()


@pytest.mark.parametrize("name", ALL_ENTITY_NAMES)
def test_entity_file_exists(name):
    assert (FIXTURES_DIR / name / f"{name}.json").exists()


def test_relations_file_exists():
    assert (FIXTURES_DIR / "relations.json").exists()


# ── Validité JSON syntaxique ──────────────────────────────────────────────────

@pytest.mark.parametrize("name", ALL_ENTITY_NAMES)
def test_entity_is_valid_json(name):
    content = (FIXTURES_DIR / name / f"{name}.json").read_text(encoding="utf-8")
    json.loads(content)


def test_relations_is_valid_json():
    content = (FIXTURES_DIR / "relations.json").read_text(encoding="utf-8")
    json.loads(content)


# ── schema_version : toujours "1.0", jamais legacy ───────────────────────────

@pytest.mark.parametrize("name", ALL_ENTITY_NAMES)
def test_entity_has_schema_version_1_0(name):
    data = json.loads((FIXTURES_DIR / name / f"{name}.json").read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


def test_relations_has_schema_version_1_0():
    data = json.loads((FIXTURES_DIR / "relations.json").read_text(encoding="utf-8"))
    assert data.get("schema_version") == "1.0"


# ── Absence de clés legacy ────────────────────────────────────────────────────

def _all_keys(obj) -> set[str]:
    keys: set[str] = set()
    if isinstance(obj, dict):
        keys |= set(obj.keys())
        for v in obj.values():
            keys |= _all_keys(v)
    elif isinstance(obj, list):
        for item in obj:
            keys |= _all_keys(item)
    return keys


@pytest.mark.parametrize("name", ALL_ENTITY_NAMES)
def test_entity_has_no_legacy_keys(name):
    data = json.loads((FIXTURES_DIR / name / f"{name}.json").read_text(encoding="utf-8"))
    found = _all_keys(data) & LEGACY_KEYS
    assert not found, f"{name}.json contient des clés legacy : {found}"


def test_relations_has_no_legacy_keys():
    data = json.loads((FIXTURES_DIR / "relations.json").read_text(encoding="utf-8"))
    found = _all_keys(data) & LEGACY_KEYS
    assert not found, f"relations.json contient des clés legacy : {found}"


# ── Couverture des cas structurants ───────────────────────────────────────────

def test_has_simple_entity():
    """Au moins une entité buildable avec un seul champ."""
    for name in BUILD_ENTITY_NAMES:
        data = json.loads((FIXTURES_DIR / name / f"{name}.json").read_text(encoding="utf-8"))
        if len(data.get("fields", [])) == 1:
            return
    pytest.fail("Aucune entité à champ unique trouvée dans les fixtures buildables")


def test_relations_has_many_to_one():
    data = json.loads((FIXTURES_DIR / "relations.json").read_text(encoding="utf-8"))
    types = [r.get("type") for r in data.get("relations", [])]
    assert "many_to_one" in types


def test_relations_has_many_to_many():
    data = json.loads((FIXTURES_DIR / "relations.json").read_text(encoding="utf-8"))
    types = [r.get("type") for r in data.get("relations", [])]
    assert "many_to_many" in types


def test_relations_has_pivot_with_fields():
    data = json.loads((FIXTURES_DIR / "relations.json").read_text(encoding="utf-8"))
    for rel in data.get("relations", []):
        if rel.get("pivot", {}).get("fields"):
            return
    pytest.fail("Aucun pivot avec fields[] non vide trouvé dans les fixtures")


# ── Validation entity:validate sur copie temporaire ──────────────────────────

def test_entity_validate_passes(tmp_project):
    pytest.importorskip("jsonschema")
    from cli.entities.entity_validate import collect_entity_validation_results
    results = collect_entity_validation_results(tmp_project)
    assert results is not None
    assert results["errors"] == [], f"Erreurs de validation : {results['errors']}"
    assert results["files_valid"] > 0


# ── build:model sur copie temporaire ─────────────────────────────────────────

def test_build_model_succeeds(built_project):
    from cli.entities.model import BuildModelResult, build_model
    result = build_model(built_project)
    assert isinstance(result, BuildModelResult)


def test_relations_sql_generated(built_project):
    assert (built_project / "relations.sql").exists()


def test_pivot_sql_contains_table(built_project):
    sql = (built_project / "relations.sql").read_text(encoding="utf-8")
    assert "member_project" in sql


def test_pivot_fields_role_in_sql(built_project):
    sql = (built_project / "relations.sql").read_text(encoding="utf-8")
    assert "role" in sql


def test_pivot_fields_joined_at_in_sql(built_project):
    sql = (built_project / "relations.sql").read_text(encoding="utf-8")
    assert "joined_at" in sql
