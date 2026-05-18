"""Garde-fou ENTITY-CONTRACT-015-FIX.

Vérifie que validate_relations_definition() traite explicitement les relations
many_to_one canoniques (schema_version 1.0) sans les ignorer silencieusement,
et produit le SQL FK attendu via generate_relations_sql().
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.entities.relations import (
    EntityRelationsError,
    ValidatedRelation,
    generate_relations_sql,
    validate_relations_definition,
)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write_entity(root: Path, name: str, data: dict) -> None:
    entity_dir = root / name.lower()
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{name.lower()}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _article_entity() -> dict:
    return {
        "format_version": 1,
        "entity": "Article",
        "table": "article",
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
                "name": "category_id",
                "column": "category_id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": True,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _article_entity_no_fk_field() -> dict:
    """Article sans champ category_id — FK column non déclarée dans l'entité."""
    return {
        "format_version": 1,
        "entity": "Article",
        "table": "article",
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
        ],
    }


def _category_entity() -> dict:
    return {
        "format_version": 1,
        "entity": "Category",
        "table": "category",
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
        "format_version": 1,
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


def _contact_entity() -> dict:
    return {
        "format_version": 1,
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


def _canonical_article_category(on_delete: str = "restrict") -> dict:
    return {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "nullable": True,
                "on_delete": on_delete,
                "index": True,
            }
        ],
    }


def _legacy_commande_contact() -> dict:
    return {
        "format_version": 1,
        "relations": [
            {
                "name": "commande_contact",
                "type": "many_to_one",
                "from_entity": "Commande",
                "to_entity": "Contact",
                "from_field": "contact_id",
                "to_field": "id",
                "foreign_key_name": "fk_commande_contact",
                "on_delete": "RESTRICT",
                "on_update": "CASCADE",
            }
        ],
    }


def _setup_article_category(tmp_path: Path, article_entity: dict | None = None) -> Path:
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Article", article_entity or _article_entity())
    _write_entity(entities_root, "Category", _category_entity())
    return entities_root


# ── Pas de skip silencieux ────────────────────────────────────────────────────

def test_canonical_many_to_one_is_not_silently_skipped(tmp_path):
    """validate_relations_definition retourne une liste non vide pour une relation canonique."""
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert len(result) == 1, "La relation canonique ne doit pas être ignorée silencieusement"


def test_canonical_many_to_one_returns_validated_relation(tmp_path):
    """validate_relations_definition retourne un ValidatedRelation pour une relation canonique."""
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert isinstance(result[0], ValidatedRelation)


# ── Génération SQL ────────────────────────────────────────────────────────────

def test_canonical_many_to_one_produces_alter_table_sql(tmp_path):
    """generate_relations_sql produit un ALTER TABLE pour une relation canonique."""
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "ALTER TABLE" in sql
    assert "FOREIGN KEY" in sql


def test_canonical_many_to_one_sql_uses_correct_tables(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "ALTER TABLE article" in sql
    assert "REFERENCES category" in sql


def test_canonical_foreign_key_column_used_in_sql(tmp_path):
    """La colonne foreign_key canonique est utilisée dans le FOREIGN KEY SQL."""
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "FOREIGN KEY (category_id)" in sql


# ── Conversion on_delete lowercase → SQL ─────────────────────────────────────

def test_canonical_on_delete_restrict(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(on_delete="restrict"),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "ON DELETE RESTRICT" in sql


def test_canonical_on_delete_cascade(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(on_delete="cascade"),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "ON DELETE CASCADE" in sql


def test_canonical_on_delete_set_null(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(on_delete="set_null"),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "ON DELETE SET NULL" in sql


def test_canonical_on_delete_no_action(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    validated = validate_relations_definition(
        _canonical_article_category(on_delete="no_action"),
        source="relations.json",
        entities_root=entities_root,
    )
    sql = generate_relations_sql(validated)
    assert "ON DELETE NO ACTION" in sql


def test_canonical_on_delete_invalid_raises(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "nullable": True,
                "on_delete": "RESTRICT",  # uppercase invalide en canonique
                "index": True,
            }
        ],
    }
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(doc, source="relations.json", entities_root=entities_root)


# ── Clés legacy non requises ──────────────────────────────────────────────────

def test_canonical_no_legacy_keys_required(tmp_path):
    """Un many_to_one canonique ne nécessite aucune clé legacy."""
    entities_root = _setup_article_category(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "nullable": True,
                "on_delete": "restrict",
                "index": True,
            }
        ],
    }
    result = validate_relations_definition(doc, source="relations.json", entities_root=entities_root)
    assert len(result) == 1


# ── FK column absente de l'entité source ──────────────────────────────────────

def test_canonical_fk_column_not_in_entity_still_generates_sql(tmp_path):
    """Si la FK column n'est pas déclarée comme champ, la SQL FK est quand même générée."""
    entities_root = _setup_article_category(tmp_path, article_entity=_article_entity_no_fk_field())
    validated = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert len(validated) == 1
    sql = generate_relations_sql(validated)
    assert "FOREIGN KEY (category_id)" in sql


# ── Support legacy many_to_one préservé ───────────────────────────────────────

def test_legacy_many_to_one_still_supported(tmp_path):
    """Le format legacy many_to_one continue de fonctionner."""
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Commande", _commande_entity())
    _write_entity(entities_root, "Contact", _contact_entity())
    result = validate_relations_definition(
        _legacy_commande_contact(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert len(result) == 1
    assert isinstance(result[0], ValidatedRelation)
    sql = generate_relations_sql(result)
    assert "ALTER TABLE commande" in sql
    assert "FOREIGN KEY (contact_id)" in sql


# ── ValidatedRelation — attributs produits ────────────────────────────────────

def test_canonical_validated_relation_from_entity(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert result[0].from_entity == "Article"


def test_canonical_validated_relation_to_entity(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert result[0].to_entity == "Category"


def test_canonical_validated_relation_from_column(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert result[0].from_column == "category_id"


def test_canonical_validated_relation_to_column(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert result[0].to_column == "id"


def test_canonical_validated_relation_type(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    result = validate_relations_definition(
        _canonical_article_category(),
        source="relations.json",
        entities_root=entities_root,
    )
    assert result[0].relation_type == "many_to_one"


# ── Détection de doublon ──────────────────────────────────────────────────────

def test_canonical_duplicate_name_raises(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "nullable": True,
                "on_delete": "restrict",
                "index": True,
            },
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",  # duplicate name
                "foreign_key": "other_id",
                "nullable": True,
                "on_delete": "restrict",
                "index": True,
            },
        ],
    }
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(doc, source="relations.json", entities_root=entities_root)


def test_canonical_duplicate_foreign_key_raises(tmp_path):
    entities_root = _setup_article_category(tmp_path)
    doc = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "category",
                "foreign_key": "category_id",
                "nullable": True,
                "on_delete": "restrict",
                "index": True,
            },
            {
                "type": "many_to_one",
                "from": "Article",
                "to": "Category",
                "name": "other_category",
                "foreign_key": "category_id",  # duplicate FK column
                "nullable": True,
                "on_delete": "restrict",
                "index": True,
            },
        ],
    }
    with pytest.raises(EntityRelationsError):
        validate_relations_definition(doc, source="relations.json", entities_root=entities_root)
