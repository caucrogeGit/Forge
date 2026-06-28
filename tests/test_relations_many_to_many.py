"""Tests REL-M2M-001/002 — declaration et SQL many_to_many.

Depuis LEGACY-REMOVE-002, le format format_version: 1 est refusé.
Les tests ci-dessous vérifient le rejet du format legacy et le bon
fonctionnement du format canonique (schema_version: "1.0").
"""

import json
from pathlib import Path

import pytest

from cli.entities.relations import (
    EntityRelationsError,
    ValidatedRelation,
    generate_relations_sql,
    validate_relations_definition,
)
from cli.entities.model import sync_relations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_entity(root: Path, name: str, data: dict) -> None:
    entity_dir = root / name.lower()
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{name.lower()}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _minimal_entity(name: str, table: str) -> dict:
    return {
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


def _contact_entity() -> dict:
    return {
        "entity": "Contact",
        "table": "contact",
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


def _commande_entity() -> dict:
    return {
        "entity": "Commande",
        "table": "commande",
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
            },
            {
                "name": "contact_id",
                "column": "contact_id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _legacy_m2m_doc() -> dict:
    """Document legacy avec format_version: 1 — refusé depuis LEGACY-REMOVE-002."""
    return {
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


def _canonical_m2m_doc() -> dict:
    """Document canonique schema_version: 1.0 — accepté."""
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
                    "fields": [],
                },
            }
        ],
    }


def _canonical_m2o_commande_contact() -> dict:
    """M2O canonique Commande → Contact."""
    return {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Commande",
                "to": "Contact",
                "name": "contact",
                "foreign_key": "contact_id",
                "nullable": False,
                "on_delete": "restrict",
            }
        ],
    }


# ---------------------------------------------------------------------------
# Rejet du format legacy (format_version: 1)
# ---------------------------------------------------------------------------


def _assert_format_version_rejected(tmp_path: Path, doc: dict) -> None:
    entities_root = tmp_path / "entities"
    entities_root.mkdir(exist_ok=True)
    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            doc,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )
    assert "format_version" in str(exc_info.value)


def test_legacy_m2m_format_version_is_rejected(tmp_path: Path):
    _assert_format_version_rejected(tmp_path, _legacy_m2m_doc())


def test_legacy_m2m_with_pivot_fields_is_rejected(tmp_path: Path):
    doc = _legacy_m2m_doc()
    doc["relations"][0]["pivot_fields"] = [{"name": "position", "sql_type": "INT", "nullable": False}]
    _assert_format_version_rejected(tmp_path, doc)


def test_legacy_m2m_missing_source_is_rejected(tmp_path: Path):
    doc = _legacy_m2m_doc()
    del doc["relations"][0]["source"]
    _assert_format_version_rejected(tmp_path, doc)


def test_legacy_m2m_missing_pivot_table_is_rejected(tmp_path: Path):
    doc = _legacy_m2m_doc()
    del doc["relations"][0]["pivot_table"]
    _assert_format_version_rejected(tmp_path, doc)


def test_legacy_m2m_unknown_type_is_rejected(tmp_path: Path):
    doc = {
        "format_version": 1,
        "relations": [{"type": "one_to_one", "from_entity": "Contact", "to_entity": "Commande"}],
    }
    _assert_format_version_rejected(tmp_path, doc)


def test_legacy_m2m_and_m2o_mixed_doc_is_rejected(tmp_path: Path):
    doc = {
        "format_version": 1,
        "relations": [
            {"type": "many_to_many", "source": "article", "target": "tag",
             "pivot_table": "article_tag", "source_key": "article_id", "target_key": "tag_id"},
            {"name": "commande_contact", "type": "many_to_one",
             "from_entity": "Commande", "to_entity": "Contact",
             "from_field": "contact_id", "to_field": "id",
             "foreign_key_name": "fk_commande_contact", "on_delete": "RESTRICT", "on_update": "CASCADE"},
        ],
    }
    _assert_format_version_rejected(tmp_path, doc)


def test_legacy_m2m_multiple_pivot_tables_doc_is_rejected(tmp_path: Path):
    doc = {
        "format_version": 1,
        "relations": [
            {"type": "many_to_many", "source": "article", "target": "tag",
             "pivot_table": "article_tag", "source_key": "article_id", "target_key": "tag_id"},
            {"type": "many_to_many", "source": "article", "target": "category",
             "pivot_table": "article_category", "source_key": "article_id", "target_key": "category_id"},
        ],
    }
    _assert_format_version_rejected(tmp_path, doc)


# ---------------------------------------------------------------------------
# Format canonique — many_to_one
# ---------------------------------------------------------------------------


def test_many_to_one_canonical_is_accepted(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    relations = validate_relations_definition(
        _canonical_m2o_commande_contact(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert len(relations) == 1
    rel = relations[0]
    assert isinstance(rel, ValidatedRelation)
    assert rel.relation_type == "many_to_one"
    assert rel.from_entity == "Commande"
    assert rel.to_entity == "Contact"

    sql = generate_relations_sql(relations)
    assert "ALTER TABLE commande" in sql
    assert "ADD CONSTRAINT fk_commande_contact" in sql


# ---------------------------------------------------------------------------
# Format canonique — many_to_many
# ---------------------------------------------------------------------------


def _setup_article_tag_entities(entities_root: Path) -> None:
    _write_entity(entities_root, "Article", _minimal_entity("Article", "article"))
    _write_entity(entities_root, "Tag", _minimal_entity("Tag", "tag"))


def test_canonical_m2m_generates_pivot_table_sql(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _setup_article_tag_entities(entities_root)

    relations = validate_relations_definition(
        _canonical_m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)
    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "article_id INT NOT NULL" in sql
    assert "tag_id INT NOT NULL" in sql
    assert "PRIMARY KEY (id)" in sql
    assert "UNIQUE KEY uq_article_tag (article_id, tag_id)" in sql
    assert "CONSTRAINT fk_article_tag_article_id" in sql
    assert "FOREIGN KEY (article_id)" in sql
    assert "CONSTRAINT fk_article_tag_tag_id" in sql
    assert "FOREIGN KEY (tag_id)" in sql


def test_canonical_m2m_sql_is_stable_between_calls(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _setup_article_tag_entities(entities_root)

    relations = validate_relations_definition(
        _canonical_m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert generate_relations_sql(relations) == generate_relations_sql(relations)


def test_canonical_m2m_does_not_generate_crud_artefacts(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _setup_article_tag_entities(entities_root)

    relations = validate_relations_definition(
        _canonical_m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)
    assert "ChoiceField" not in sql
    assert "<select" not in sql
    assert "class ArticleTag" not in sql


# ---------------------------------------------------------------------------
# sync_relations avec format canonique
# ---------------------------------------------------------------------------


def test_sync_relations_writes_canonical_m2m_pivot_sql(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _setup_article_tag_entities(entities_root)
    (entities_root / "relations.json").write_text(
        json.dumps(_canonical_m2m_doc(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    output = sync_relations(entities_root)

    assert output == entities_root / "relations.sql"
    sql = output.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "PRIMARY KEY (id)" in sql


def test_sync_relations_rejects_legacy_format(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir(exist_ok=True)
    (entities_root / "relations.json").write_text(
        json.dumps(_legacy_m2m_doc(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(EntityRelationsError) as exc_info:
        sync_relations(entities_root)
    assert "format_version" in str(exc_info.value)


def test_canonical_m2m_sql_sqlite_executes(monkeypatch):
    """Le pivot généré sous SQLite est idiomatique (INTEGER PK, UNIQUE, CREATE
    INDEX séparés) et s'exécute réellement dans sqlite3."""
    pytest.importorskip("forge_mvc_sqlite")
    import sqlite3

    from core.database import backend as backend_module
    from cli.entities.relations import (
        ValidatedCanonicalManyToManyRelation,
        _generate_canonical_m2m_sql,
    )

    relation = ValidatedCanonicalManyToManyRelation(
        from_entity="Article",
        from_table="article",
        to_entity="Tag",
        to_table="tag",
        pivot_table="article_tag",
        from_key="article_id",
        to_key="tag_id",
        on_delete="CASCADE",
    )

    monkeypatch.setenv("DB_BACKEND", "sqlite")
    backend_module.reset_backend()
    try:
        sql = _generate_canonical_m2m_sql(relation)
    finally:
        backend_module.reset_backend()

    assert "INTEGER PRIMARY KEY AUTOINCREMENT" in sql
    assert "UNIQUE KEY" not in sql  # forme MariaDB absente
    assert "UNIQUE (article_id, tag_id)" in sql
    assert "CREATE INDEX IF NOT EXISTS idx_article_tag_article_id ON article_tag (article_id);" in sql

    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE article (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE tag (id INTEGER PRIMARY KEY)")
        conn.executescript(sql)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(article_tag)")}
        assert {"id", "article_id", "tag_id"} <= cols
    finally:
        conn.close()
