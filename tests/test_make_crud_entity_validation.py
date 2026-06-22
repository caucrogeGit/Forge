"""Garde-fou ENTITY-CONTRACT-012.

Vérifie que make:crud valide les contrats JSON Schema avant génération.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from cli.entities.make_crud import make_crud

PROJECT_ROOT = Path(__file__).parent.parent

_VALID_CANONICAL = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "title", "type": "string", "max_length": 255, "required": True},
    ],
}

_INVALID_ENTITY = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "articles",
    "fields": [
        {"name": "id", "type": "integer"},
    ],
}

_RELATIONS_CANONICAL = {
    "schema_version": "1.0",
    "relations": [],
}

_INVALID_RELATIONS = {
    "schema_version": "1.0",
    "relations": [
        {"type": "one_to_one", "from": "Article", "to": "User", "name": "author"},
    ],
}


def _setup(tmp_path: Path, entity_data: dict, relations_data: dict | None = None) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    article_dir = entities_root / "article"
    article_dir.mkdir(parents=True)
    (article_dir / "article.json").write_text(
        json.dumps(entity_data), encoding="utf-8"
    )
    (entities_root / "relations.json").write_text(
        json.dumps(relations_data or _RELATIONS_CANONICAL), encoding="utf-8"
    )
    return entities_root


# ── Projet valide — génération autorisée ─────────────────────────────────────

def test_valid_project_make_crud_returns_result(tmp_path):
    entities_root = _setup(tmp_path, _VALID_CANONICAL)
    result = make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    from cli.entities.make_crud import MakeCrudResult
    assert isinstance(result, MakeCrudResult)


def test_valid_project_generates_controller(tmp_path):
    entities_root = _setup(tmp_path, _VALID_CANONICAL)
    make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


def test_valid_project_generates_model(tmp_path):
    entities_root = _setup(tmp_path, _VALID_CANONICAL)
    make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert (tmp_path / "mvc" / "models" / "article_model.py").exists()


def test_valid_project_generates_form(tmp_path):
    entities_root = _setup(tmp_path, _VALID_CANONICAL)
    make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert (tmp_path / "mvc" / "forms" / "article_form.py").exists()


# ── Entité invalide — génération bloquée ─────────────────────────────────────

def test_invalid_entity_raises_system_exit(tmp_path):
    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    with pytest.raises(SystemExit) as exc_info:
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert exc_info.value.code != 0


def test_invalid_entity_no_files_generated(tmp_path):
    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert not (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()
    assert not (tmp_path / "mvc" / "models" / "article_model.py").exists()
    assert not (tmp_path / "mvc" / "forms" / "article_form.py").exists()


def test_invalid_entity_message_has_entity_validate(tmp_path, capsys):
    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    captured = capsys.readouterr()
    assert "entity:validate" in captured.out


def test_invalid_entity_message_is_short(tmp_path, capsys):
    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    captured = capsys.readouterr()
    assert "FORGE_ENTITY_SCHEMA_INVALID" not in captured.out
    assert "Additional properties" not in captured.out


def test_invalid_entity_no_python_traceback(tmp_path, capsys):
    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out


# ── Relations invalides — génération bloquée ──────────────────────────────────

def test_invalid_relations_raises_system_exit(tmp_path):
    entities_root = _setup(tmp_path, _VALID_CANONICAL, _INVALID_RELATIONS)
    with pytest.raises(SystemExit) as exc_info:
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert exc_info.value.code != 0


def test_invalid_relations_no_files_generated(tmp_path):
    entities_root = _setup(tmp_path, _VALID_CANONICAL, _INVALID_RELATIONS)
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    assert not (tmp_path / "mvc" / "controllers" / "article_controller.py").exists()


def test_invalid_relations_message_has_entity_validate(tmp_path, capsys):
    entities_root = _setup(tmp_path, _VALID_CANONICAL, _INVALID_RELATIONS)
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    captured = capsys.readouterr()
    assert "entity:validate" in captured.out


# ── API collect_entity_validation_results — diagnostic détaillé préservé ─────

def test_entity_validate_still_detailed(tmp_path):
    """collect_entity_validation_results retourne les erreurs complètes."""
    from cli.entities.entity_validate import collect_entity_validation_results

    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    results = collect_entity_validation_results(entities_root)

    if results is None:
        pytest.skip("jsonschema non disponible")

    assert results["errors"]
    first = results["errors"][0]
    assert "code" in first
    assert "file" in first
    assert "message" in first


def test_entity_validate_json_output_unchanged():
    """Le format --json de entity:validate n'est pas affecté par 012."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    for key in ("valid", "files_checked", "files_valid", "errors_count", "warnings_count", "errors", "warnings"):
        assert key in output, f"Clé manquante : {key}"
