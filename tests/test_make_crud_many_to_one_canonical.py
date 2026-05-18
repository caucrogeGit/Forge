"""Garde-fou ENTITY-CONTRACT-015-FIX-CRUD-CANONICAL-M2O.

Vérifie que make:crud fonctionne avec une relation many_to_one canonique
même si la clé étrangère n'est pas déclarée comme champ métier dans l'entité source.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_cli.entities.crud.relations_loader import _load_crud_many_to_one_relations
from forge_cli.entities.make_crud import (
    MakeCrudResult,
    build_controller,
    build_form,
    make_crud,
    _to_snake,
)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _write_entity(root: Path, name: str, data: dict) -> None:
    entity_dir = root / name.lower()
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{name.lower()}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n", encoding="utf-8"
    )


def _article_no_fk() -> dict:
    """Article sans champ category_id — FK technique non déclarée."""
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
                "name": "title",
                "column": "title",
                "python_type": "str",
                "sql_type": "VARCHAR(255)",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _article_with_fk() -> dict:
    """Article avec category_id déclaré comme champ métier."""
    entity = _article_no_fk()
    entity["fields"].append({
        "name": "category_id",
        "column": "category_id",
        "python_type": "int",
        "sql_type": "INT",
        "nullable": True,
        "primary_key": False,
        "auto_increment": False,
        "constraints": {},
    })
    return entity


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
            },
            {
                "name": "name",
                "column": "name",
                "python_type": "str",
                "sql_type": "VARCHAR(255)",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _canonical_relations() -> dict:
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
                "on_delete": "restrict",
                "index": True,
            }
        ],
    }


def _setup_entities(tmp_path: Path, *, article: dict | None = None) -> Path:
    entities_root = tmp_path / "mvc" / "entities"
    _write_entity(entities_root, "Article", article or _article_no_fk())
    _write_entity(entities_root, "Category", _category_entity())
    (entities_root / "relations.json").write_text(
        json.dumps(_canonical_relations(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )
    return entities_root


# ── Pas de KeyError ────────────────────────────────────────────────────────────

def test_canonical_m2o_without_fk_field_does_not_raise(tmp_path):
    """_load_crud_many_to_one_relations ne lève pas KeyError quand FK absente des champs."""
    entities_root = _setup_entities(tmp_path)
    definition = _article_no_fk()
    result = _load_crud_many_to_one_relations(definition, entities_root)
    assert len(result) == 1


def test_canonical_m2o_field_column_is_foreign_key(tmp_path):
    """field_column utilise la valeur de foreign_key quand le champ n'est pas déclaré."""
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    assert result[0].field_column == "category_id"


def test_canonical_m2o_field_name_is_foreign_key(tmp_path):
    """field_name correspond à la colonne FK canonique."""
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    assert result[0].field_name == "category_id"


def test_canonical_m2o_target_entity(tmp_path):
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    assert result[0].target_entity == "Category"


def test_canonical_m2o_target_table(tmp_path):
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    assert result[0].target_table == "category"


def test_canonical_m2o_target_pk_column(tmp_path):
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    assert result[0].target_pk_column == "id"


def test_canonical_m2o_choices_function(tmp_path):
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    assert result[0].choices_function == "get_category_choices"


# ── Avec FK déclarée dans les champs ──────────────────────────────────────────

def test_canonical_m2o_with_fk_field_declared_uses_field_column(tmp_path):
    """Si la FK est déclarée dans les champs, field_column vient du champ (column key)."""
    entities_root = _setup_entities(tmp_path, article=_article_with_fk())
    result = _load_crud_many_to_one_relations(_article_with_fk(), entities_root)
    assert result[0].field_column == "category_id"


def test_canonical_m2o_with_fk_field_declared_returns_relation(tmp_path):
    entities_root = _setup_entities(tmp_path, article=_article_with_fk())
    result = _load_crud_many_to_one_relations(_article_with_fk(), entities_root)
    assert len(result) == 1


# ── Intégration make_crud ─────────────────────────────────────────────────────

def test_make_crud_with_canonical_m2o_does_not_raise(monkeypatch, tmp_path):
    """make_crud ne lève pas SystemExit avec une relation canonique sans FK dans les champs."""
    monkeypatch.chdir(tmp_path)
    entities_root = _setup_entities(tmp_path)
    result = make_crud("Article", entities_root=entities_root, output_root=tmp_path, dry_run=True)
    assert isinstance(result, MakeCrudResult)


def test_make_crud_with_canonical_m2o_build_form_does_not_raise(tmp_path):
    """build_form ne lève pas d'exception avec une relation canonique sans FK déclarée."""
    entities_root = _setup_entities(tmp_path)
    relations = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    form_code, _warnings = build_form(_article_no_fk(), relations)
    # Quand la FK n'est pas déclarée comme champ, build_form génère le formulaire
    # sans RelationField pour cette FK (comportement attendu — FK technique invisible du formulaire).
    assert "ArticleForm" in form_code
    assert isinstance(form_code, str)


def test_make_crud_with_canonical_m2o_generates_choices_in_controller(tmp_path):
    """build_controller génère get_category_choices pour la FK canonique."""
    entities_root = _setup_entities(tmp_path)
    relations = _load_crud_many_to_one_relations(_article_no_fk(), entities_root)
    controller_code = build_controller(_article_no_fk(), relations)
    assert "get_category_choices" in controller_code


# ── Support legacy préservé ───────────────────────────────────────────────────

def test_legacy_m2o_still_supported(tmp_path):
    """Le format legacy many_to_one continue de fonctionner."""
    entities_root = tmp_path / "mvc" / "entities"
    contact = {
        "format_version": 1,
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {"name": "id", "column": "id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True, "constraints": {}},
            {"name": "ville_id", "column": "VilleId", "python_type": "int", "sql_type": "INT",
             "nullable": True, "primary_key": False, "auto_increment": False, "constraints": {}},
        ],
    }
    ville = {
        "format_version": 1,
        "entity": "Ville",
        "table": "ville",
        "description": "",
        "fields": [
            {"name": "id", "column": "Id", "python_type": "int", "sql_type": "INT",
             "nullable": False, "primary_key": True, "auto_increment": True, "constraints": {}},
            {"name": "nom", "column": "Nom", "python_type": "str", "sql_type": "VARCHAR(100)",
             "nullable": False, "primary_key": False, "auto_increment": False, "constraints": {}},
        ],
    }
    legacy_relations = {
        "format_version": 1,
        "relations": [{
            "name": "contact_ville",
            "type": "many_to_one",
            "from_entity": "Contact",
            "to_entity": "Ville",
            "from_field": "ville_id",
            "to_field": "id",
            "foreign_key_name": "fk_contact_ville",
            "on_delete": "SET NULL",
            "on_update": "CASCADE",
        }],
    }
    _write_entity(entities_root, "Contact", contact)
    _write_entity(entities_root, "Ville", ville)
    (entities_root / "relations.json").write_text(json.dumps(legacy_relations), encoding="utf-8")

    result = _load_crud_many_to_one_relations(contact, entities_root)
    assert len(result) == 1
    assert result[0].field_name == "ville_id"
    assert result[0].field_column == "VilleId"
    assert result[0].target_entity == "Ville"


# ── Aucun diagnostic many_to_many ajouté ─────────────────────────────────────

def test_canonical_m2o_does_not_affect_many_to_many_loader(tmp_path):
    """_load_crud_many_to_many_relations retourne vide pour une relation many_to_one canonique."""
    from forge_cli.entities.crud.relations_loader import _load_crud_many_to_many_relations
    entities_root = _setup_entities(tmp_path)
    result = _load_crud_many_to_many_relations(_article_no_fk(), entities_root)
    assert result == []
