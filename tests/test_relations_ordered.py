"""Tests REL-ORDERED-001 — relations many_to_many avec order_column.

Depuis LEGACY-REMOVE-002, le format format_version: 1 est refusé et
order_column (feature legacy) est supprimé.
Ces tests vérifient le rejet du format legacy pour toutes les variantes.
"""

import json
from pathlib import Path

import pytest

from cli.entities.make_crud import make_crud, _to_snake
from cli.entities.relations import (
    EntityRelationsError,
    validate_relations_definition,
)


# ---------------------------------------------------------------------------
# Helpers communs
# ---------------------------------------------------------------------------


def _write_entity(root: Path, definition: dict) -> None:
    snake = _to_snake(definition["entity"])
    entity_dir = root / snake
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")


def _legacy_m2m(order_column: str | None = None, pivot_fields: list | None = None) -> dict:
    rel: dict = {
        "type": "many_to_many",
        "source": "article",
        "target": "tag",
        "pivot_table": "article_tag",
        "source_key": "article_id",
        "target_key": "tag_id",
    }
    if pivot_fields is not None:
        rel["pivot_fields"] = pivot_fields
    if order_column is not None:
        rel["order_column"] = order_column
    return rel


def _legacy_doc(relation: dict) -> dict:
    return {"format_version": 1, "relations": [relation]}


def _assert_rejected(tmp_path: Path, relation: dict) -> None:
    entities_root = tmp_path / "entities"
    entities_root.mkdir(exist_ok=True)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            _legacy_doc(relation),
            source="relations.json",
            entities_root=entities_root,
        )
    assert "format_version" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Rejet : schéma — order_column absent ou présent (format legacy refusé)
# ---------------------------------------------------------------------------


def test_legacy_m2m_without_order_column_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}]
    ))


def test_legacy_m2m_no_pivot_fields_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m())


def test_legacy_m2m_with_valid_order_column_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    ))


def test_legacy_m2m_order_column_two_fields_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        order_column="position",
        pivot_fields=[
            {"name": "position", "sql_type": "INT", "nullable": False},
            {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
        ],
    ))


def test_legacy_m2m_order_column_pointing_non_first_field_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        order_column="note",
        pivot_fields=[
            {"name": "position", "sql_type": "INT", "nullable": False},
            {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
        ],
    ))


def test_legacy_m2m_empty_order_column_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        order_column="",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    ))


def test_legacy_m2m_invalid_identifier_order_column_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        order_column="ma colonne",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    ))


def test_legacy_m2m_no_pivot_fields_with_order_column_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(order_column="position"))


def test_legacy_m2m_nonexistent_order_column_field_is_rejected(tmp_path):
    _assert_rejected(tmp_path, _legacy_m2m(
        order_column="sort_order",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    ))


def test_legacy_m2m_null_order_column_is_rejected(tmp_path):
    rel = _legacy_m2m(pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}])
    rel["order_column"] = None
    _assert_rejected(tmp_path, rel)


def test_legacy_m2m_numeric_order_column_is_rejected(tmp_path):
    rel = _legacy_m2m(pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}])
    rel["order_column"] = 42
    _assert_rejected(tmp_path, rel)


# ---------------------------------------------------------------------------
# Rejet : génération CRUD (make_crud lève SystemExit sur format legacy)
# ---------------------------------------------------------------------------


_ARTICLE = {
    "entity": "Article",
    "table": "article",
    "description": "",
    "fields": [
        {
            "name": "id",
            "column": "Id",
            "python_type": "int",
            "sql_type": "INT",
            "nullable": False,
            "primary_key": True,
            "auto_increment": True,
            "constraints": {},
            "unique": False,
        },
        {
            "name": "title",
            "column": "Title",
            "python_type": "str",
            "sql_type": "VARCHAR(150)",
            "nullable": False,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
            "unique": False,
        },
    ],
}

_TAG = {
    "entity": "Tag",
    "table": "tag",
    "description": "",
    "fields": [
        {
            "name": "id",
            "column": "Id",
            "python_type": "int",
            "sql_type": "INT",
            "nullable": False,
            "primary_key": True,
            "auto_increment": True,
            "constraints": {},
            "unique": False,
        },
        {
            "name": "name",
            "column": "Name",
            "python_type": "str",
            "sql_type": "VARCHAR(80)",
            "nullable": False,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
            "unique": False,
        },
    ],
}


def _assert_make_crud_rejects_legacy(tmp_path: Path, relation: dict) -> None:
    entities_root = tmp_path / "mvc" / "entities"
    for definition in (_ARTICLE, _TAG):
        snake = _to_snake(definition["entity"])
        entity_dir = entities_root / snake
        entity_dir.mkdir(parents=True, exist_ok=True)
        (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")
    (entities_root / "relations.json").write_text(
        json.dumps({"format_version": 1, "relations": [relation]}), encoding="utf-8"
    )
    with pytest.raises(SystemExit):
        make_crud("Article", entities_root=entities_root, output_root=tmp_path)


def test_make_crud_rejects_legacy_m2m_without_order_column(tmp_path):
    _assert_make_crud_rejects_legacy(tmp_path, _legacy_m2m(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}]
    ))


def test_make_crud_rejects_legacy_m2m_with_order_column(tmp_path):
    _assert_make_crud_rejects_legacy(tmp_path, _legacy_m2m(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    ))


def test_make_crud_rejects_legacy_m2m_no_pivot_fields(tmp_path):
    _assert_make_crud_rejects_legacy(tmp_path, _legacy_m2m())


def test_make_crud_rejects_legacy_m2m_order_column_other_field(tmp_path):
    _assert_make_crud_rejects_legacy(tmp_path, _legacy_m2m(
        order_column="display_order",
        pivot_fields=[
            {"name": "position", "sql_type": "INT", "nullable": False},
            {"name": "display_order", "sql_type": "SMALLINT", "nullable": False},
        ],
    ))
