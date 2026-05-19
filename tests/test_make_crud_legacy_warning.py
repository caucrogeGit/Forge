"""Tests LEGACY-WARNINGS-004 — warning non bloquant dans make_crud pour entités legacy."""

from __future__ import annotations

import json
from pathlib import Path

from forge_cli.entities.make_crud import make_crud

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


# ── Warning présent pour entité legacy ───────────────────────────────────────


class TestLegacyWarningPresent:
    def test_make_crud_legacy_produces_warning(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        assert any("legacy" in w.lower() or "format_version" in w for w in result.warnings)

    def test_warning_mentions_format_version(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        legacy_warns = [w for w in result.warnings if "format_version" in w]
        assert legacy_warns

    def test_warning_mentions_schema_version(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        legacy_warns = [w for w in result.warnings if "schema_version" in w]
        assert legacy_warns

    def test_warning_mentions_deprecation(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        legacy_warns = [w for w in result.warnings if "déprécié" in w or "deprecated" in w]
        assert legacy_warns

    def test_warning_mentions_migration_guide(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        legacy_warns = [w for w in result.warnings if "migration" in w.lower() or "Guide" in w]
        assert legacy_warns

    def test_warning_exposed_in_result_warnings(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        assert isinstance(result.warnings, list)
        assert len(result.warnings) >= 1


# ── Génération CRUD inchangée ─────────────────────────────────────────────────


class TestLegacyGenerationUnchanged:
    def test_make_crud_still_generates_files(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=False)
        assert result.created or result.preserved
        controller = tmp_path / "mvc" / "controllers" / "contact_controller.py"
        assert controller.exists()

    def test_warning_does_not_block_generation(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=False)
        legacy_warns = [w for w in result.warnings if "format_version" in w]
        assert legacy_warns
        assert (tmp_path / "mvc" / "models" / "contact_model.py").exists()

    def test_warning_is_exactly_one_for_single_entity(self, tmp_path):
        entities_root = _setup(tmp_path, _legacy_entity())
        result = make_crud("Contact", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        legacy_warns = [w for w in result.warnings if "format_version" in w]
        assert len(legacy_warns) == 1


# ── Pas de warning pour entité canonique ──────────────────────────────────────


class TestCanonicalNoLegacyWarning:
    def test_canonical_entity_no_legacy_warning(self, tmp_path):
        entities_root = _setup(tmp_path, _canonical_entity(), _CANONICAL_RELATIONS)
        result = make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=True)
        legacy_warns = [w for w in result.warnings if "format_version" in w or "legacy" in w.lower()]
        assert legacy_warns == []

    def test_canonical_entity_generates_without_warning(self, tmp_path):
        entities_root = _setup(tmp_path, _canonical_entity(), _CANONICAL_RELATIONS)
        result = make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=False)
        legacy_warns = [w for w in result.warnings if "format_version" in w]
        assert legacy_warns == []
        assert result.created or result.preserved
