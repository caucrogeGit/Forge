"""Garde-fou ENTITY-CONTRACT-011C.

Vérifie que build:model route les entités canoniques (schema_version 1.0)
via le normaliseur, et refuse les entités legacy (format_version: 1).

Couverture :
- entité legacy format_version: 1 → ModelValidationError
- entité canonique → normaliseur appelé, génération OK
- SQL et _base.py générés depuis le format canonique
- entité canonique invalide → ModelValidationError claire
- entité sans version → chemin legacy non bloquant
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.entities.model import BuildModelResult, ModelValidationError, build_model, check_model

pytestmark = pytest.mark.meta

_CANONICAL_RELATIONS = {"schema_version": "1.0", "relations": []}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _write_relations(root: Path, data: dict) -> None:
    (root / "relations.json").write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def _canonical_article(fields=None, options=None):
    data = {
        "schema_version": "1.0",
        "name": "Article",
        "table": "articles",
        "fields": fields or [{"name": "title", "type": "string", "max_length": 255, "required": True}],
    }
    if options:
        data["options"] = options
    return data


def _legacy_contact():
    return {
        "format_version": 1,
        "entity": "Contact",
        "table": "contact",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            }
        ],
    }


# ── Legacy refusé ─────────────────────────────────────────────────────────────

class TestLegacyRejected:
    def test_legacy_entity_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_contact())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)

    def test_legacy_build_model_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_contact())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            build_model(entities_root)

    def test_legacy_no_sql_generated(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_contact())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            build_model(entities_root)
        assert not (entities_root / "contact" / "contact.sql").exists()

    def test_legacy_invalid_entity_rejected(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        bad = {
            "entity": "contact",
            "fields": [{"name": "id", "sql_type": "INT", "primary_key": True}],
        }
        _write_entity(entities_root, "contact", bad)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)


# ── Routage canonique ─────────────────────────────────────────────────────────

class TestCanonicalRouting:
    def test_canonical_entity_loads_without_error(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert len(sources) == 1

    def test_canonical_name_becomes_entity(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert sources[0].definition["entity"] == "Article"

    def test_canonical_table_preserved(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert sources[0].definition["table"] == "articles"

    def test_canonical_id_added_automatically(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        defn = sources[0].definition
        id_field = next((f for f in defn["fields"] if f["name"] == "id"), None)
        assert id_field is not None
        assert id_field["primary_key"] is True
        assert id_field["auto_increment"] is True

    def test_canonical_build_model_succeeds(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        result = build_model(entities_root)
        assert isinstance(result, BuildModelResult)
        assert entities_root / "article" / "article.sql" in result.written
        assert entities_root / "article" / "article_base.py" in result.written

    def test_canonical_sql_contains_primary_key(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        sql = (entities_root / "article" / "article.sql").read_text(encoding="utf-8")
        assert "PRIMARY KEY" in sql

    def test_canonical_sql_contains_title_varchar(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        sql = (entities_root / "article" / "article.sql").read_text(encoding="utf-8")
        assert "VARCHAR(255)" in sql

    def test_canonical_sql_no_missing_sql_type_error(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        sql = (entities_root / "article" / "article.sql").read_text(encoding="utf-8")
        assert "None" not in sql

    def test_canonical_base_py_generated(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        base_py = (entities_root / "article" / "article_base.py").read_text(encoding="utf-8")
        assert "class ArticleBase" in base_py

    def test_canonical_base_py_contains_title_field(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        base_py = (entities_root / "article" / "article_base.py").read_text(encoding="utf-8")
        assert "title" in base_py

    def test_canonical_base_py_contains_id_field(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        base_py = (entities_root / "article" / "article_base.py").read_text(encoding="utf-8")
        assert "self.id" in base_py

    def test_canonical_dry_run_does_not_write(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root, dry_run=True)
        assert not (entities_root / "article" / "article.sql").exists()
        assert not (entities_root / "article" / "article_base.py").exists()

    def test_canonical_timestamps_fields_in_base_py(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        entity = _canonical_article(options={"timestamps": True})
        _write_entity(entities_root, "article", entity)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        build_model(entities_root)
        base_py = (entities_root / "article" / "article_base.py").read_text(encoding="utf-8")
        assert "created_at" in base_py
        assert "updated_at" in base_py

    def test_canonical_all_forge_types_generate(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        entity = _canonical_article(fields=[
            {"name": "title", "type": "string", "max_length": 100},
            {"name": "body", "type": "text"},
            {"name": "count", "type": "integer"},
            {"name": "score", "type": "float"},
            {"name": "active", "type": "boolean"},
            {"name": "birth_date", "type": "date"},
            {"name": "published_at", "type": "datetime"},
        ])
        _write_entity(entities_root, "article", entity)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        result = build_model(entities_root)
        assert entities_root / "article" / "article.sql" in result.written


# ── Legacy dans un projet mixte bloque tout ───────────────────────────────────

class TestLegacyInMixedProject:
    def test_legacy_in_mixed_project_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "contact", _legacy_contact())
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)

    def test_canonical_only_project_succeeds(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        _write_entity(entities_root, "article", _canonical_article())
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        result = build_model(entities_root)
        assert entities_root / "article" / "article.sql" in result.written
        assert entities_root / "article" / "article_base.py" in result.written


# ── Cas d'erreur ──────────────────────────────────────────────────────────────

class TestErrorHandling:
    def test_invalid_canonical_unknown_type_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        invalid = _canonical_article(fields=[{"name": "broken", "type": "unknown_forge_type"}])
        _write_entity(entities_root, "article", invalid)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)

    def test_invalid_canonical_decimal_missing_precision_raises(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        invalid = _canonical_article(fields=[{"name": "price", "type": "decimal"}])
        _write_entity(entities_root, "article", invalid)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError) as exc_info:
            check_model(entities_root)
        msg = str(exc_info.value).lower()
        assert "decimal" in msg or "price" in msg

    def test_invalid_canonical_error_is_model_validation_not_traceback(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        invalid = _canonical_article(fields=[{"name": "x", "type": "bad_type"}])
        _write_entity(entities_root, "article", invalid)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)

    def test_invalid_legacy_still_rejected(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        bad_legacy = {
            "entity": "contact",
            "fields": [{"name": "id", "sql_type": "INT", "primary_key": True}],
        }
        _write_entity(entities_root, "contact", bad_legacy)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        with pytest.raises(ModelValidationError):
            check_model(entities_root)

    def test_no_version_falls_through_legacy(self, tmp_path):
        entities_root = tmp_path / "mvc" / "entities"
        no_version = {
            "entity": "Contact",
            "table": "contact",
            "fields": [{"name": "id", "sql_type": "INT", "primary_key": True, "auto_increment": True}],
        }
        _write_entity(entities_root, "contact", no_version)
        _write_relations(entities_root, _CANONICAL_RELATIONS)
        sources, _ = check_model(entities_root)
        assert sources[0].definition["entity"] == "Contact"
