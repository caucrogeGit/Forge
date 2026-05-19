"""Tests LEGACY-WARNINGS-002 — warning non bloquant dans build_model pour entités legacy."""

from __future__ import annotations

import json
from pathlib import Path

from forge_cli.entities.model import BuildModelResult, build_model, check_model

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


# ── Warning présent pour une entité legacy ────────────────────────────────────


class TestLegacyWarningPresent:
    def test_build_model_legacy_produces_warning(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert len(result.legacy_warnings) == 1

    def test_warning_mentions_format_version(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert "format_version" in result.legacy_warnings[0]

    def test_warning_mentions_schema_version(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert 'schema_version' in result.legacy_warnings[0]

    def test_warning_mentions_deprecation(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        w = result.legacy_warnings[0]
        assert "déprécié" in w or "deprecated" in w

    def test_warning_mentions_entity_name(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity("Contact"))
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert "Contact" in result.legacy_warnings[0]

    def test_warning_mentions_migration_guide(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert "migration" in result.legacy_warnings[0].lower() or "Guide" in result.legacy_warnings[0]


# ── Génération SQL non affectée ───────────────────────────────────────────────


class TestLegacyGenerationUnchanged:
    def test_build_model_still_generates_sql(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert isinstance(result, BuildModelResult)
        assert entities_root / "contact" / "contact.sql" in result.written

    def test_build_model_sql_content_correct(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        build_model(entities_root)
        sql = (entities_root / "contact" / "contact.sql").read_text(encoding="utf-8")
        assert "Id INT NOT NULL" in sql

    def test_legacy_warning_does_not_block_generation(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert result.legacy_warnings
        assert (entities_root / "contact" / "contact.sql").exists()


# ── Pas de warning pour une entité canonique ─────────────────────────────────


class TestCanonicalNoWarning:
    def test_canonical_entity_no_warning(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_entity())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        result = build_model(entities_root)
        assert result.legacy_warnings == []

    def test_canonical_entity_is_not_legacy(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_entity())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert all(not s.is_legacy for s in sources)


# ── Plusieurs entités legacy → un warning par entité ─────────────────────────


class TestMultipleLegacyEntities:
    def test_two_legacy_entities_two_warnings(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity("Contact", "contact"))
        _write_entity(entities_root, "produit", _legacy_entity("Produit", "produit"))
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert len(result.legacy_warnings) == 2

    def test_mixed_project_warning_only_for_legacy(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_entity("Article", "articles"))
        _write_entity(entities_root, "contact", _legacy_entity("Contact", "contact"))
        _write_relations(entities_root, _LEGACY_RELATIONS)
        result = build_model(entities_root)
        assert len(result.legacy_warnings) == 1
        assert "Contact" in result.legacy_warnings[0]


# ── is_legacy sur EntitySource ────────────────────────────────────────────────


class TestEntitySourceIsLegacy:
    def test_legacy_source_is_marked(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_entity())
        _write_relations(entities_root, _LEGACY_RELATIONS)
        sources, _ = check_model(entities_root)
        assert sources[0].is_legacy is True

    def test_canonical_source_not_marked(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_entity())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert sources[0].is_legacy is False
