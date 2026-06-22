"""Garde-fou ENTITY-CONTRACT-017-PIVOT-FIELDS-CONTROLLED.

Vérifie que pivot.fields[] dans les relations many_to_many canoniques est
validé, mappe correctement vers SQL, et protège les clés techniques.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from cli.entities.relations import (
    EntityRelationsError,
    ValidatedCanonicalManyToManyRelation,
    generate_relations_sql,
    validate_relations_definition,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_entity(root: Path, folder: str, data: dict) -> None:
    entity_dir = root / folder
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{folder}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _minimal_entity(name: str, table: str) -> dict:
    return {
        "format_version": 1,
        "entity": name,
        "table": table,
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            }
        ],
    }


def _setup_entities(tmp_path: Path) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "article", _minimal_entity("Article", "article"))
    _write_entity(entities_root, "tag", _minimal_entity("Tag", "tag"))
    return entities_root


def _doc(fields: list[dict[str, Any]]) -> dict:
    return {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": fields,
                },
            }
        ],
    }


def _validate(tmp_path: Path, fields: list[dict]) -> list:
    entities_root = _setup_entities(tmp_path)
    return validate_relations_definition(
        _doc(fields), source="test", entities_root=entities_root
    )


def _sql(tmp_path: Path, fields: list[dict]) -> str:
    result = _validate(tmp_path, fields)
    return generate_relations_sql(result)


# ── Acceptation des types Forge ────────────────────────────────────────────────

@pytest.mark.parametrize("forge_type,expected_sql_fragment", [
    ("text",        "TEXT"),
    ("integer",     "INT"),
    ("big_integer", "BIGINT"),
    ("float",       "DOUBLE"),
    ("boolean",     "BOOLEAN"),
    ("date",        "DATE"),
    ("datetime",    "DATETIME"),
    ("email",       "VARCHAR(255)"),
    ("password",    "VARCHAR(255)"),
    ("json",        "LONGTEXT"),
])
def test_simple_forge_type_accepted(tmp_path, forge_type, expected_sql_fragment):
    """Chaque type Forge simple est accepté dans pivot.fields[]."""
    result = _validate(tmp_path, [{"name": "attr", "type": forge_type}])
    assert len(result) == 1
    assert isinstance(result[0], ValidatedCanonicalManyToManyRelation)
    assert len(result[0].pivot_fields) == 1
    assert expected_sql_fragment in result[0].pivot_fields[0].sql_type


def test_string_type_accepted(tmp_path):
    """Le type 'string' est accepté avec max_length."""
    result = _validate(tmp_path, [{"name": "role", "type": "string", "max_length": 50}])
    assert len(result[0].pivot_fields) == 1
    assert result[0].pivot_fields[0].sql_type == "VARCHAR(50)"


def test_decimal_type_accepted(tmp_path):
    """Le type 'decimal' est accepté avec precision et scale."""
    result = _validate(tmp_path, [{"name": "amount", "type": "decimal", "precision": 10, "scale": 2}])
    assert len(result[0].pivot_fields) == 1
    assert result[0].pivot_fields[0].sql_type == "DECIMAL(10,2)"


# ── Mapping SQL ────────────────────────────────────────────────────────────────

def test_string_with_max_length_generates_varchar(tmp_path):
    sql = _sql(tmp_path, [{"name": "role", "type": "string", "max_length": 50}])
    assert "role VARCHAR(50)" in sql


def test_string_without_max_length_defaults_to_varchar_255(tmp_path):
    sql = _sql(tmp_path, [{"name": "role", "type": "string"}])
    assert "role VARCHAR(255)" in sql


def test_decimal_generates_decimal_pq(tmp_path):
    sql = _sql(tmp_path, [{"name": "amount", "type": "decimal", "precision": 8, "scale": 3}])
    assert "amount DECIMAL(8,3)" in sql


def test_boolean_generates_boolean(tmp_path):
    sql = _sql(tmp_path, [{"name": "active", "type": "boolean"}])
    assert "active BOOLEAN" in sql


def test_integer_generates_int(tmp_path):
    sql = _sql(tmp_path, [{"name": "score", "type": "integer"}])
    assert "score INT" in sql


def test_big_integer_generates_bigint(tmp_path):
    sql = _sql(tmp_path, [{"name": "big_count", "type": "big_integer"}])
    assert "big_count BIGINT" in sql


def test_datetime_generates_datetime(tmp_path):
    sql = _sql(tmp_path, [{"name": "joined_at", "type": "datetime"}])
    assert "joined_at DATETIME" in sql


def test_json_generates_longtext(tmp_path):
    sql = _sql(tmp_path, [{"name": "meta", "type": "json"}])
    assert "meta LONGTEXT" in sql


# ── Contraintes nullable / required ───────────────────────────────────────────

def test_required_true_generates_not_null(tmp_path):
    sql = _sql(tmp_path, [{"name": "role", "type": "string", "max_length": 50, "required": True}])
    assert "role VARCHAR(50) NOT NULL" in sql


def test_nullable_false_generates_not_null(tmp_path):
    sql = _sql(tmp_path, [{"name": "role", "type": "string", "max_length": 50, "nullable": False}])
    assert "role VARCHAR(50) NOT NULL" in sql


def test_nullable_true_generates_null(tmp_path):
    sql = _sql(tmp_path, [{"name": "note", "type": "text", "nullable": True}])
    assert "note TEXT NULL" in sql


def test_default_nullable_is_nullable(tmp_path):
    """Sans nullable ni required, le champ est nullable (field.schema.json default = true)."""
    result = _validate(tmp_path, [{"name": "role", "type": "string"}])
    assert result[0].pivot_fields[0].nullable is True


def test_nullable_field_attribute(tmp_path):
    result = _validate(tmp_path, [{"name": "role", "type": "string", "nullable": False}])
    assert result[0].pivot_fields[0].nullable is False


# ── Contrainte unique ──────────────────────────────────────────────────────────

def test_unique_true_generates_unique_key(tmp_path):
    sql = _sql(tmp_path, [{"name": "role", "type": "string", "max_length": 50, "unique": True}])
    assert "UNIQUE KEY uq_article_tag_role" in sql


def test_unique_false_no_unique_key(tmp_path):
    sql = _sql(tmp_path, [{"name": "role", "type": "string", "max_length": 50, "unique": False}])
    assert "UNIQUE KEY uq_article_tag_role" not in sql


def test_unique_field_attribute(tmp_path):
    result = _validate(tmp_path, [{"name": "role", "type": "string", "unique": True}])
    assert result[0].pivot_fields[0].unique is True


# ── Protection des clés techniques ────────────────────────────────────────────

def test_pivot_fields_cannot_redeclare_id(tmp_path):
    """pivot.fields[] ne peut pas redéclarer 'id'."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            _doc([{"name": "id", "type": "integer"}]),
            source="test",
            entities_root=entities_root,
        )
    assert "nom reserve interdit" in str(exc_info.value)


def test_pivot_fields_cannot_redeclare_from_key(tmp_path):
    """pivot.fields[] ne peut pas redéclarer from_key (article_id)."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            _doc([{"name": "article_id", "type": "integer"}]),
            source="test",
            entities_root=entities_root,
        )
    assert "nom reserve interdit" in str(exc_info.value)


def test_pivot_fields_cannot_redeclare_to_key(tmp_path):
    """pivot.fields[] ne peut pas redéclarer to_key (tag_id)."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            _doc([{"name": "tag_id", "type": "integer"}]),
            source="test",
            entities_root=entities_root,
        )
    assert "nom reserve interdit" in str(exc_info.value)


def test_entity_validate_fails_stable_on_reserved_collision(tmp_path):
    """EntityRelationsError est levée avec un message stable pour les collisions."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            _doc([{"name": "id", "type": "integer"}]),
            source="test",
            entities_root=entities_root,
        )
    err = str(exc_info.value)
    assert "test" in err
    assert "nom reserve interdit" in err


def test_entity_validate_passes_with_valid_pivot_fields(tmp_path):
    """validate_relations_definition ne lève pas d'erreur avec des champs pivot valides."""
    result = _validate(tmp_path, [
        {"name": "role", "type": "string", "max_length": 50, "required": True},
        {"name": "joined_at", "type": "datetime", "nullable": True},
    ])
    assert len(result) == 1
    assert len(result[0].pivot_fields) == 2


# ── Type invalide ──────────────────────────────────────────────────────────────

def test_unknown_type_raises(tmp_path):
    """Un type Forge inconnu dans pivot.fields[] lève EntityRelationsError."""
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(
            _doc([{"name": "attr", "type": "uuid"}]),
            source="test",
            entities_root=entities_root,
        )


def test_missing_type_raises(tmp_path):
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(
            _doc([{"name": "attr"}]),
            source="test",
            entities_root=entities_root,
        )


def test_decimal_missing_precision_raises(tmp_path):
    entities_root = _setup_entities(tmp_path)
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(
            _doc([{"name": "amount", "type": "decimal", "scale": 2}]),
            source="test",
            entities_root=entities_root,
        )


# ── SQL complet du pivot ───────────────────────────────────────────────────────

def test_build_model_generates_pivot_with_fields(tmp_path):
    """generate_relations_sql génère la table pivot avec les colonnes pivot."""
    sql = _sql(tmp_path, [
        {"name": "role", "type": "string", "max_length": 50, "required": True},
        {"name": "joined_at", "type": "datetime", "nullable": True},
    ])
    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "role VARCHAR(50) NOT NULL" in sql
    assert "joined_at DATETIME NULL" in sql
    assert "PRIMARY KEY (id)" in sql
    assert "UNIQUE KEY uq_article_tag (article_id, tag_id)" in sql


def test_pivot_fields_appear_before_primary_key(tmp_path):
    """Les colonnes pivot apparaissent avant la PRIMARY KEY dans le SQL."""
    sql = _sql(tmp_path, [{"name": "role", "type": "string"}])
    role_pos = sql.index("role")
    pk_pos = sql.index("PRIMARY KEY")
    assert role_pos < pk_pos


def test_multiple_pivot_fields_all_present_in_sql(tmp_path):
    sql = _sql(tmp_path, [
        {"name": "role", "type": "string", "max_length": 30},
        {"name": "score", "type": "integer"},
        {"name": "active", "type": "boolean"},
    ])
    assert "role VARCHAR(30)" in sql
    assert "score INT" in sql
    assert "active BOOLEAN" in sql


# ── Non-régression ─────────────────────────────────────────────────────────────

def test_m2m_without_fields_still_works(tmp_path):
    """many_to_many sans fields continue de fonctionner."""
    entities_root = _setup_entities(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_many",
                "from": "Article",
                "to": "Tag",
                "name": "tags",
                "pivot": {
                    "table": "article_tag",
                    "from_key": "article_id",
                    "to_key": "tag_id",
                    "id": True,
                    "unique_pair": True,
                    "on_delete": "cascade",
                    "fields": [],
                },
            }
        ],
    }
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert len(result) == 1
    assert result[0].pivot_fields == ()


def test_m2o_canonical_not_affected(tmp_path):
    """many_to_one canonique n'est pas régressé."""
    entities_root = _setup_entities(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Tag",
                "to": "Article",
                "name": "article",
                "foreign_key": "article_id",
                "on_delete": "restrict",
            }
        ],
    }
    result = validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert len(result) == 1
    assert result[0].relation_type == "many_to_one"


def test_legacy_m2m_not_affected(tmp_path):
    """Legacy many_to_many (format_version: 1) est désormais refusé."""
    from cli.entities.relations import EntityRelationsError
    entities_root = _setup_entities(tmp_path)
    doc = {
        "format_version": 1,
        "relations": [
            {
                "type": "many_to_many",
                "source": "article",
                "target": "tag",
                "pivot_table": "article_tag",
                "source_key": "article_id",
                "target_key": "tag_id",
            }
        ],
    }
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(doc, source="test", entities_root=entities_root)
    assert "format_version" in str(exc_info.value)
