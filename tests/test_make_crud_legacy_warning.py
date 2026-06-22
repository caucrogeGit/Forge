"""Tests LEGACY-REMOVE-001B — make:crud refuse les entités format_version: 1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from cli.entities.make_crud import make_crud

_LEGACY_RELATIONS = {"format_version": 1, "relations": []}
_CANONICAL_RELATIONS = {"schema_version": "1.0", "relations": []}


def _setup(tmp_path: Path, entity_data: dict, relations_data: dict | None = None) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    snake = entity_data.get("entity", entity_data.get("name", "contact")).lower()
    entity_dir = entities_root / snake
    entity_dir.mkdir(parents=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(entity_data), encoding="utf-8")
    (entities_root / "relations.json").write_text(
        json.dumps(relations_data or _LEGACY_RELATIONS), encoding="utf-8"
    )
    return entities_root


def _legacy_entity(name: str = "Contact", table: str = "contact") -> dict:
    return {
        "format_version": 1,
        "entity": name,
        "table": table,
        "fields": [
            {"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True},
            {"name": "nom", "sql_type": "VARCHAR(120)", "constraints": {"not_empty": True}},
        ],
    }


def _canonical_entity(name: str = "Article", table: str = "articles") -> dict:
    return {
        "schema_version": "1.0",
        "name": name,
        "table": table,
        "fields": [{"name": "title", "type": "string", "max_length": 255, "required": True}],
    }


# ── make:crud refuse les entités format_version: 1 ───────────────────────────


class TestLegacyEntityRejected:
    def test_make_crud_legacy_raises_system_exit(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        with pytest.raises(SystemExit):
            make_crud("Contact", entities_root=entities_root, output_root=tmp_path)

    def test_error_output_mentions_format_version(self, tmp_path, capsys):
        entities_root = _setup(tmp_path, _legacy_entity())
        with pytest.raises(SystemExit):
            make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
        assert "format_version" in capsys.readouterr().out

    def test_error_output_mentions_schema_version(self, tmp_path, capsys):
        entities_root = _setup(tmp_path, _legacy_entity())
        with pytest.raises(SystemExit):
            make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
        assert "schema_version" in capsys.readouterr().out

    def test_make_crud_dry_run_also_rejects_legacy(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        with pytest.raises(SystemExit):
            make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)


# ── Aucun fichier CRUD généré pour une entité legacy ─────────────────────────


class TestLegacyNoGeneration:
    def test_no_controller_created(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        with pytest.raises(SystemExit):
            make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
        assert not (tmp_path / "mvc" / "controllers" / "contact_controller.py").exists()

    def test_no_model_created(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        with pytest.raises(SystemExit):
            make_crud("Contact", entities_root=entities_root, output_root=tmp_path)
        assert not (tmp_path / "mvc" / "models" / "contact_model.py").exists()


# ── Entité canonique toujours acceptée ───────────────────────────────────────


class TestCanonicalAccepted:
    def test_canonical_entity_succeeds(self, tmp_path):
        entities_root = _setup(tmp_path, _canonical_entity(), _CANONICAL_RELATIONS)
        result = make_crud("Article", entities_root=entities_root, output_root=tmp_path)
        assert result.created or result.preserved

    def test_canonical_entity_no_format_version_in_warnings(self, tmp_path):
        entities_root = _setup(tmp_path, _canonical_entity(), _CANONICAL_RELATIONS)
        result = make_crud("Article", entities_root=entities_root, output_root=tmp_path)
        assert not any("format_version" in w for w in result.warnings)
