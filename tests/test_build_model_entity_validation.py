"""Garde-fou ENTITY-CONTRACT-011G.

Vérifie que build:model bloque la génération si les contrats JSON Schema
sont invalides, et qu'il aboutit normalement si les contrats sont valides.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent

_VALID_CANONICAL = {
    "$schema": "../../schemas/entity.schema.json",
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "title", "type": "string", "max_length": 255, "required": True},
    ],
}

_INVALID_SCHEMA = {
    "$schema": "../../schemas/entity.schema.json",
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "id", "type": "integer"},
    ],
}

_RELATIONS_CANONICAL = {
    "$schema": "../../schemas/relations.schema.json",
    "schema_version": "1.0",
    "relations": [],
}


def _setup_entities(tmp_path: Path, entity_data: dict) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    article_dir = entities_root / "article"
    article_dir.mkdir(parents=True)
    (article_dir / "article.json").write_text(
        json.dumps(entity_data), encoding="utf-8"
    )
    (entities_root / "relations.json").write_text(
        json.dumps(_RELATIONS_CANONICAL), encoding="utf-8"
    )
    return entities_root


# ── Projet valide — la génération doit réussir ───────────────────────────────

def test_valid_project_build_succeeds(tmp_path):
    from forge_mvc_entities.model import BuildModelResult, build_model

    entities_root = _setup_entities(tmp_path, _VALID_CANONICAL)
    result = build_model(entities_root)

    assert isinstance(result, BuildModelResult)


def test_valid_project_generates_model(tmp_path):
    from forge_mvc_entities.model import build_model

    entities_root = _setup_entities(tmp_path, _VALID_CANONICAL)
    build_model(entities_root)

    assert (entities_root / "article" / "article.sql").exists()
    assert (entities_root / "article" / "article_base.py").exists()
    assert (entities_root / "relations.sql").exists()


# ── Projet invalide — la génération doit être bloquée ────────────────────────

def test_invalid_schema_build_raises(tmp_path):
    from forge_mvc_entities.model import ModelValidationError, build_model

    entities_root = _setup_entities(tmp_path, _INVALID_SCHEMA)

    with pytest.raises(ModelValidationError):
        build_model(entities_root)


def test_invalid_schema_no_files_generated(tmp_path):
    from forge_mvc_entities.model import ModelValidationError, build_model

    entities_root = _setup_entities(tmp_path, _INVALID_SCHEMA)

    with pytest.raises(ModelValidationError):
        build_model(entities_root)

    assert not (entities_root / "article" / "article.sql").exists()
    assert not (entities_root / "article" / "article_base.py").exists()


def test_invalid_schema_message_contains_entity_validate_advice(tmp_path):
    from forge_mvc_entities.model import ModelValidationError, build_model

    entities_root = _setup_entities(tmp_path, _INVALID_SCHEMA)

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)

    assert "entity:validate" in str(exc_info.value)


def test_invalid_schema_message_is_short(tmp_path):
    from forge_mvc_entities.model import ModelValidationError, build_model

    entities_root = _setup_entities(tmp_path, _INVALID_SCHEMA)

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)

    msg = str(exc_info.value)
    assert "FORGE_ENTITY_SCHEMA_INVALID" not in msg
    assert "Additional properties" not in msg


def test_invalid_schema_no_python_traceback(tmp_path):
    from forge_mvc_entities.model import ModelValidationError, build_model

    entities_root = _setup_entities(tmp_path, _INVALID_SCHEMA)

    with pytest.raises(ModelValidationError) as exc_info:
        build_model(entities_root)

    assert "Traceback" not in str(exc_info.value)


# ── Dépôt réel — non-régression ──────────────────────────────────────────────

def test_real_repo_build_model_succeeds():
    from forge_mvc_entities.model import build_model

    entities_root = PROJECT_ROOT / "tests" / "fixtures" / "app" / "mvc" / "entities"
    result = build_model(entities_root, dry_run=True)

    assert result.dry_run is True


def test_real_repo_entity_validate_valid():
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "forge.py"), "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT / "tests" / "fixtures" / "app"),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    assert output.get("valid") is True


# ── collect_entity_validation_results — API programmatique ───────────────────

def test_entity_validate_still_detailed(tmp_path):
    """collect_entity_validation_results retourne les erreurs complètes."""
    from forge_mvc_entities.entity_validate import collect_entity_validation_results

    entities_root = _setup_entities(tmp_path, _INVALID_SCHEMA)
    results = collect_entity_validation_results(entities_root)

    if results is None:
        pytest.skip("jsonschema non disponible")

    assert results["errors"]
    first = results["errors"][0]
    assert "code" in first
    assert "file" in first
    assert "message" in first


def test_entity_validate_json_output_unchanged():
    """Le format --json de entity:validate est inchangé après 011G."""
    result = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "forge.py"), "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT / "tests" / "fixtures" / "app"),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)

    for key in ("valid", "files_checked", "files_valid", "errors_count", "warnings_count", "errors", "warnings"):
        assert key in output, f"Clé manquante dans --json : {key}"
