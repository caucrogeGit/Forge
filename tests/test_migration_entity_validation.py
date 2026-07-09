"""Garde-fou ENTITY-CONTRACT-013.

Vérifie que migration:diff et migration:make --from-diff valident les contrats
JSON Schema avant génération ou comparaison depuis les entités.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from forge_mvc_entities import migrations

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


# ── Table de couverture (audit codé) ─────────────────────────────────────────

def test_audit_protected_commands_documented():
    """Vérifie que migration:diff et migration:make --from-diff lisent load_entity_definition."""
    source = Path(migrations.__file__).read_text(encoding="utf-8")
    assert "_run_diff_command" in source
    assert "_assert_migration_contracts_valid" in source


# ── migration:diff — entité invalide — bloqué ────────────────────────────────

def test_migration_diff_invalid_entity_raises(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        migrations.main(["migration:diff", "--entity", "Article"])
    assert exc_info.value.code != 0


def test_migration_diff_invalid_entity_message_has_entity_validate(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        migrations.main(["migration:diff", "--entity", "Article"])
    captured = capsys.readouterr()
    assert "entity:validate" in captured.out


def test_migration_diff_invalid_entity_message_is_short(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        migrations.main(["migration:diff", "--entity", "Article"])
    captured = capsys.readouterr()
    assert "FORGE_ENTITY_SCHEMA_INVALID" not in captured.out
    assert "Additional properties" not in captured.out


def test_migration_diff_invalid_entity_no_traceback(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        migrations.main(["migration:diff", "--entity", "Article"])
    captured = capsys.readouterr()
    assert "Traceback" not in captured.out


# ── migration:diff — relations invalides — bloqué ────────────────────────────

def test_migration_diff_invalid_relations_raises(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _VALID_CANONICAL, _INVALID_RELATIONS)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        migrations.main(["migration:diff", "--entity", "Article"])
    assert exc_info.value.code != 0
    assert "entity:validate" in capsys.readouterr().out


# ── migration:diff — projet valide — le garde passe ──────────────────────────

def test_migration_diff_valid_entity_passes_guard(tmp_path, monkeypatch, capsys):
    """Avec entité valide, le garde passe (la commande échoue ensuite sur DB)."""
    _setup(tmp_path, _VALID_CANONICAL)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        migrations.main(["migration:diff", "--entity", "Article"])
    captured = capsys.readouterr()
    assert "entity:validate" not in captured.out


# ── migration:make --from-diff — entité invalide — bloqué ────────────────────

def test_migration_make_from_diff_invalid_entity_raises(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        migrations.main(["migration:make", "test", "--from-diff", "Article"])
    assert exc_info.value.code != 0
    assert "entity:validate" in capsys.readouterr().out


def test_migration_make_from_diff_invalid_entity_no_files(tmp_path, monkeypatch):
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    migrations_dir = tmp_path / "mvc" / "migrations"
    with pytest.raises(SystemExit):
        migrations.main(["migration:make", "test", "--from-diff", "Article"])
    assert not migrations_dir.exists() or not list(migrations_dir.glob("*.sql"))


def test_migration_make_from_diff_invalid_relations_raises(tmp_path, monkeypatch, capsys):
    _setup(tmp_path, _VALID_CANONICAL, _INVALID_RELATIONS)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit) as exc_info:
        migrations.main(["migration:make", "test", "--from-diff", "Article"])
    assert exc_info.value.code != 0
    assert "entity:validate" in capsys.readouterr().out


def test_migration_make_from_diff_valid_entity_passes_guard(tmp_path, monkeypatch, capsys):
    """Avec entité valide, le garde passe (la commande échoue ensuite sur DB)."""
    _setup(tmp_path, _VALID_CANONICAL)
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        migrations.main(["migration:make", "test", "--from-diff", "Article"])
    captured = capsys.readouterr()
    assert "entity:validate" not in captured.out


# ── Commandes non protégées — migration:make (blank) ─────────────────────────

def test_migration_make_blank_not_guarded(tmp_path, monkeypatch):
    """migration:make (blank) n'est pas protégé — ne lit pas les entités JSON."""
    _setup(tmp_path, _INVALID_ENTITY)
    monkeypatch.chdir(tmp_path)
    migrations.main(["migration:make", "test_migration"])
    migration_files = list((tmp_path / "mvc" / "migrations").glob("*.sql"))
    assert len(migration_files) == 1


# ── API collect_entity_validation_results — diagnostic détaillé préservé ─────

def test_entity_validate_detailed_after_013(tmp_path):
    """collect_entity_validation_results retourne les erreurs complètes."""
    from forge_mvc_entities.entity_validate import collect_entity_validation_results
    entities_root = _setup(tmp_path, _INVALID_ENTITY)
    results = collect_entity_validation_results(entities_root)
    if results is None:
        pytest.skip("jsonschema non disponible")
    assert results["errors"]
    first = results["errors"][0]
    assert "code" in first and "file" in first and "message" in first


def test_entity_validate_json_output_unchanged_after_013():
    """Le format --json de entity:validate n'est pas affecté par 013."""
    result = subprocess.run(
        [sys.executable, "forge.py", "entity:validate", "--json"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    output = json.loads(result.stdout)
    for key in ("valid", "files_checked", "files_valid", "errors_count", "warnings_count", "errors", "warnings"):
        assert key in output, f"Clé manquante : {key}"
