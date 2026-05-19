"""Tests REL-ORDERED-001 — relations many_to_many ordonnées via order_column."""

import json
from pathlib import Path

import pytest

from forge_cli.entities.make_crud import make_crud, _to_snake
from forge_cli.entities.relations import (
    EntityRelationsError,
    ValidatedManyToManyRelation,
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


def _m2m_with_order(order_column: str | None = None, pivot_fields: list | None = None) -> dict:
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


def _doc(relation: dict) -> dict:
    return {"format_version": 1, "relations": [relation]}


def _validate(tmp_path: Path, relation: dict) -> list:
    entities_root = tmp_path / "entities"
    entities_root.mkdir(exist_ok=True)
    return validate_relations_definition(
        _doc(relation),
        source="relations.json",
        entities_root=entities_root,
    )


# ---------------------------------------------------------------------------
# Schéma — order_column absent : valeur par défaut None
# ---------------------------------------------------------------------------


def test_order_column_absent_par_defaut_none(tmp_path):
    rel = _m2m_with_order(pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}])
    relations = _validate(tmp_path, rel)
    assert isinstance(relations[0], ValidatedManyToManyRelation)
    assert relations[0].order_column is None


def test_order_column_absent_sans_pivot_fields_est_valide(tmp_path):
    rel = _m2m_with_order()
    relations = _validate(tmp_path, rel)
    assert relations[0].order_column is None


# ---------------------------------------------------------------------------
# Schéma — order_column valide
# ---------------------------------------------------------------------------


def test_order_column_valide_est_accepte(tmp_path):
    rel = _m2m_with_order(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    relations = _validate(tmp_path, rel)
    assert relations[0].order_column == "position"


def test_order_column_valide_conserve_pivot_fields(tmp_path):
    rel = _m2m_with_order(
        order_column="position",
        pivot_fields=[
            {"name": "position", "sql_type": "INT", "nullable": False},
            {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
        ],
    )
    relations = _validate(tmp_path, rel)
    assert relations[0].order_column == "position"
    assert len(relations[0].pivot_fields) == 2


def test_order_column_peut_pointer_champ_non_premier(tmp_path):
    rel = _m2m_with_order(
        order_column="note",
        pivot_fields=[
            {"name": "position", "sql_type": "INT", "nullable": False},
            {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
        ],
    )
    relations = _validate(tmp_path, rel)
    assert relations[0].order_column == "note"


# ---------------------------------------------------------------------------
# Schéma — order_column invalide : rejeté
# ---------------------------------------------------------------------------


def test_order_column_vide_est_rejete(tmp_path):
    rel = _m2m_with_order(
        order_column="",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    with pytest.raises(EntityRelationsError) as exc_info:
        _validate(tmp_path, rel)
    assert "relations[0].order_column" in str(exc_info.value)
    assert "doit etre une chaine non vide" in str(exc_info.value)


def test_order_column_non_chaine_est_rejete(tmp_path):
    rel = _m2m_with_order(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    rel["order_column"] = 42
    with pytest.raises(EntityRelationsError) as exc_info:
        _validate(tmp_path, rel)
    assert "relations[0].order_column" in str(exc_info.value)


def test_order_column_identifiant_invalide_est_rejete(tmp_path):
    rel = _m2m_with_order(
        order_column="ma colonne",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    with pytest.raises(EntityRelationsError) as exc_info:
        _validate(tmp_path, rel)
    assert "relations[0].order_column" in str(exc_info.value)
    assert "doit etre un identifiant SQL valide" in str(exc_info.value)


def test_order_column_sans_pivot_fields_est_rejete(tmp_path):
    rel = _m2m_with_order(order_column="position")
    with pytest.raises(EntityRelationsError) as exc_info:
        _validate(tmp_path, rel)
    assert "relations[0].order_column" in str(exc_info.value)
    assert "doit etre le nom d'un champ declare dans pivot_fields" in str(exc_info.value)


def test_order_column_champ_inexistant_est_rejete(tmp_path):
    rel = _m2m_with_order(
        order_column="sort_order",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    with pytest.raises(EntityRelationsError) as exc_info:
        _validate(tmp_path, rel)
    assert "relations[0].order_column" in str(exc_info.value)
    assert "doit etre le nom d'un champ declare dans pivot_fields" in str(exc_info.value)


def test_order_column_cle_inconnue_sans_valeur_est_rejete(tmp_path):
    rel = _m2m_with_order(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    rel["order_column"] = None
    with pytest.raises(EntityRelationsError) as exc_info:
        _validate(tmp_path, rel)
    assert "relations[0].order_column" in str(exc_info.value)


# ---------------------------------------------------------------------------
# Génération SQL : CREATE TABLE inchangée
# ---------------------------------------------------------------------------


def test_order_column_ne_modifie_pas_le_sql_create_table(tmp_path):
    from forge_cli.entities.relations import generate_relations_sql

    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    rel_with = _m2m_with_order(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    rel_without = _m2m_with_order(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    rels_with = validate_relations_definition(
        _doc(rel_with), source="r.json", entities_root=entities_root
    )
    rels_without = validate_relations_definition(
        _doc(rel_without), source="r.json", entities_root=entities_root
    )
    assert generate_relations_sql(rels_with) == generate_relations_sql(rels_without)


# ---------------------------------------------------------------------------
# Génération CRUD — helpers
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


def _run(tmp_path: Path, relation: dict) -> str:
    entities_root = tmp_path / "mvc" / "entities"
    for definition in (_ARTICLE, _TAG):
        snake = _to_snake(definition["entity"])
        entity_dir = entities_root / snake
        entity_dir.mkdir(parents=True, exist_ok=True)
        (entity_dir / f"{snake}.json").write_text(json.dumps(definition), encoding="utf-8")
    (entities_root / "relations.json").write_text(
        json.dumps({"format_version": 1, "relations": [relation]}), encoding="utf-8"
    )
    make_crud("Article", entities_root=entities_root, output_root=tmp_path)
    return (tmp_path / "mvc" / "models" / "article_model.py").read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Génération CRUD — sans order_column
# ---------------------------------------------------------------------------


def test_sans_order_column_order_by_sur_label_cible(tmp_path):
    rel = _m2m_with_order(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    model = _run(tmp_path, rel)
    assert "ORDER BY tag.Name" in model


def test_sans_order_column_pas_order_by_pivot(tmp_path):
    rel = _m2m_with_order(
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    model = _run(tmp_path, rel)
    assert "ORDER BY pivot.position" not in model


def test_sans_pivot_fields_order_by_sur_label_cible(tmp_path):
    model = _run(tmp_path, _m2m_with_order())
    assert "ORDER BY tag.Name" in model


# ---------------------------------------------------------------------------
# Génération CRUD — avec order_column
# ---------------------------------------------------------------------------


def test_avec_order_column_order_by_sur_pivot(tmp_path):
    rel = _m2m_with_order(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    model = _run(tmp_path, rel)
    assert "ORDER BY pivot.position" in model


def test_avec_order_column_plus_de_order_by_label_cible(tmp_path):
    rel = _m2m_with_order(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    model = _run(tmp_path, rel)
    assert "ORDER BY tag.Name" not in model


def test_order_by_pivot_dans_list_labels_function(tmp_path):
    rel = _m2m_with_order(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    model = _run(tmp_path, rel)
    assert "get_article_tag_labels_by_article_id" in model
    idx = model.index("get_article_tag_labels_by_article_id")
    fragment = model[idx : idx + 600]
    assert "ORDER BY pivot.position" in fragment


def test_order_by_pivot_dans_show_labels_function(tmp_path):
    rel = _m2m_with_order(
        order_column="position",
        pivot_fields=[{"name": "position", "sql_type": "INT", "nullable": False}],
    )
    model = _run(tmp_path, rel)
    assert "get_article_tag_labels" in model
    idx = model.rindex("get_article_tag_labels(id)")
    fragment = model[idx : idx + 500]
    assert "ORDER BY pivot.position" in fragment


def test_order_column_autre_champ_pivot(tmp_path):
    rel = _m2m_with_order(
        order_column="display_order",
        pivot_fields=[
            {"name": "position", "sql_type": "INT", "nullable": False},
            {"name": "display_order", "sql_type": "SMALLINT", "nullable": False},
        ],
    )
    model = _run(tmp_path, rel)
    assert "ORDER BY pivot.display_order" in model
    assert "ORDER BY tag.Name" not in model
