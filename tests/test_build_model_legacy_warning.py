"""Tests LEGACY-REMOVE-001A — build:model refuse les entités format_version: 1."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.entities.model import BuildModelResult, ModelValidationError, build_model, check_model

_LEGACY_RELATIONS = {"format_version": 1, "relations": []}
_CANONICAL_RELATIONS = {"schema_version": "1.0", "relations": []}


def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def _write_relations(root: Path, data: dict) -> None:
    (root / "relations.json").write_text(json.dumps(data, indent=2), encoding="utf-8")


def _legacy_entity(name: str = "Contact", table: str = "contact") -> dict:
    return {
        "format_version": 1,
        "entity": name,
        "table": table,
        "fields": [{"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True}],
    }


def _canonical_entity(name: str = "Article", table: str = "articles") -> dict:
    return {
        "schema_version": "1.0",
        "name": name,
        "table": table,
        "fields": [{"name": "title", "type": "string", "max_length": 255, "required": True}],
    }


# ── build:model lève une erreur sur format_version: 1 ────────────────────────


class TestLegacyEntityRejected:
    def test_build_model_legacy_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError):
            build_model(entities_root)

    def test_error_mentions_format_version(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError) as exc_info:
            build_model(entities_root)
        assert "format_version" in str(exc_info.value)

    def test_error_mentions_schema_version(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError) as exc_info:
            build_model(entities_root)
        assert "schema_version" in str(exc_info.value)

    def test_error_mentions_migration_guide(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError) as exc_info:
            build_model(entities_root)
        assert "migration-legacy-vers-canonique" in str(exc_info.value)

    def test_check_model_legacy_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)


# ── Aucune génération SQL pour une entité legacy ──────────────────────────────


class TestLegacyNoSqlGenerated:
    def test_no_sql_file_created(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError):
            build_model(entities_root)
        assert not (entities_root / "contact" / "contact.sql").exists()

    def test_two_legacy_entities_both_rejected(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity("Contact", "contact"))
        _write_entity(entities_root, "produit", _legacy_entity("Produit", "produit"))
        _write_relations(entities_root, _LEGACY_RELATIONS)
        with pytest.raises(ModelValidationError):
            build_model(entities_root)
        assert not (entities_root / "contact" / "contact.sql").exists()
        assert not (entities_root / "produit" / "produit.sql").exists()


# ── Entité canonique toujours acceptée ───────────────────────────────────────


class TestCanonicalAccepted:
    def test_canonical_build_model_succeeds(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_entity())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        result = build_model(entities_root)
        assert isinstance(result, BuildModelResult)
        assert entities_root / "article" / "article.sql" in result.written

    def test_canonical_check_model_succeeds(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_entity())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert len(sources) == 1
        assert sources[0].definition["entity"] == "Article"
