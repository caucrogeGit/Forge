"""Tests REL-M2M-001/002 — declaration et SQL many_to_many."""

import json
from pathlib import Path

import pytest

from forge_cli.entities.relations import (
    EntityRelationsError,
    ValidatedManyToManyRelation,
    ValidatedRelation,
    generate_relations_sql,
    validate_relations_definition,
)
from forge_cli.entities.model import sync_relations


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
        "format_version": 1,
        "entity": name,
        "table": table,
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
            }
        ],
    }


def _valid_m2m() -> dict:
    return {
        "type": "many_to_many",
        "source": "article",
        "target": "tag",
        "pivot_table": "article_tag",
        "source_key": "article_id",
        "target_key": "tag_id",
    }


def _m2m_doc(relations: list | None = None) -> dict:
    return {
        "format_version": 1,
        "relations": relations if relations is not None else [_valid_m2m()],
    }


def _m2o_doc() -> dict:
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


def _contact_entity() -> dict:
    return {
        "format_version": 1,
        "entity": "Contact",
        "table": "contact",
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
                "column": "Id",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            },
            {
                "name": "contact_id",
                "column": "ContactId",
                "python_type": "int",
                "sql_type": "INT",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


# ---------------------------------------------------------------------------
# Tests REL-M2M-001
# ---------------------------------------------------------------------------


def test_many_to_many_relation_is_accepted(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    relations = validate_relations_definition(
        _m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert len(relations) == 1
    rel = relations[0]
    assert isinstance(rel, ValidatedManyToManyRelation)
    assert rel.relation_type == "many_to_many"
    assert rel.source == "article"
    assert rel.target == "tag"
    assert rel.pivot_table == "article_tag"
    assert rel.source_key == "article_id"
    assert rel.target_key == "tag_id"
    assert rel.pivot_fields == ()


def test_many_to_many_pivot_fields_are_optional_and_accepted(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [
        {"name": "position", "sql_type": "INT", "nullable": False},
        {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
    ]

    relations = validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    rel = relations[0]
    assert isinstance(rel, ValidatedManyToManyRelation)
    assert [field.name for field in rel.pivot_fields] == ["position", "note"]
    assert [field.sql_type for field in rel.pivot_fields] == ["INT", "VARCHAR(255)"]
    assert [field.nullable for field in rel.pivot_fields] == [False, True]


def test_many_to_many_pivot_fields_must_be_a_list(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = {"name": "position"}

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_fields: doit etre une liste" in str(exc_info.value)


def test_many_to_many_pivot_fields_null_is_rejected_when_provided(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = None

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_fields: doit etre une liste" in str(exc_info.value)


def test_many_to_many_pivot_field_requires_name(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [{"sql_type": "INT"}]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_fields[0].name: cle obligatoire manquante" in str(exc_info.value)


def test_many_to_many_pivot_field_requires_sql_type(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [{"name": "position"}]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_fields[0].sql_type: cle obligatoire manquante" in str(exc_info.value)


def test_many_to_many_pivot_field_nullable_must_be_bool(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [
        {"name": "position", "sql_type": "INT", "nullable": "false"}
    ]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_fields[0].nullable: doit etre un booleen" in str(exc_info.value)


def test_many_to_many_pivot_field_cannot_duplicate_source_key(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [{"name": "article_id", "sql_type": "INT"}]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "ne doit pas dupliquer source_key ou target_key" in str(exc_info.value)


def test_many_to_many_pivot_field_cannot_duplicate_target_key(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [{"name": "tag_id", "sql_type": "INT"}]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "ne doit pas dupliquer source_key ou target_key" in str(exc_info.value)


def test_many_to_many_requires_source(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    del data["relations"][0]["source"]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].source: cle obligatoire manquante" in str(exc_info.value)


def test_many_to_many_requires_target(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    del data["relations"][0]["target"]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].target: cle obligatoire manquante" in str(exc_info.value)


def test_many_to_many_requires_pivot_table(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    del data["relations"][0]["pivot_table"]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_table: cle obligatoire manquante" in str(exc_info.value)


def test_many_to_many_requires_source_key(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    del data["relations"][0]["source_key"]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].source_key: cle obligatoire manquante" in str(exc_info.value)


def test_many_to_many_requires_target_key(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    del data["relations"][0]["target_key"]

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].target_key: cle obligatoire manquante" in str(exc_info.value)


def test_unknown_relation_type_is_rejected(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = {
        "format_version": 1,
        "relations": [
            {
                "name": "rel",
                "type": "one_to_one",
                "from_entity": "Contact",
                "to_entity": "Commande",
                "from_field": "contact_id",
                "to_field": "id",
                "foreign_key_name": "fk_rel",
                "on_delete": "RESTRICT",
                "on_update": "CASCADE",
            }
        ],
    }

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "type de relation non reconnu" in str(exc_info.value)


def test_many_to_one_existing_behavior_is_preserved(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    relations = validate_relations_definition(
        _m2o_doc(),
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


def test_many_to_many_generates_pivot_sql(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    relations = validate_relations_definition(
        _m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)
    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "article_id INT NOT NULL" in sql
    assert "tag_id INT NOT NULL" in sql
    assert "PRIMARY KEY (article_id, tag_id)" in sql
    assert "INDEX idx_article_tag_article_id (article_id)" in sql
    assert "INDEX idx_article_tag_tag_id (tag_id)" in sql
    assert "CONSTRAINT fk_article_tag_article_id" in sql
    assert "FOREIGN KEY (article_id)" in sql
    assert "REFERENCES article(id)" in sql
    assert "CONSTRAINT fk_article_tag_tag_id" in sql
    assert "FOREIGN KEY (tag_id)" in sql
    assert "REFERENCES tag(id)" in sql
    assert sql.count("ON DELETE CASCADE") == 2


def test_many_to_many_generates_pivot_fields_sql(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [
        {"name": "position", "sql_type": "INT", "nullable": False},
        {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
    ]

    relations = validate_relations_definition(
        data,
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)
    assert "article_id INT NOT NULL" in sql
    assert "tag_id INT NOT NULL" in sql
    assert "position INT NOT NULL" in sql
    assert "note VARCHAR(255) NULL" in sql
    assert sql.index("tag_id INT NOT NULL") < sql.index("position INT NOT NULL")
    assert sql.index("position INT NOT NULL") < sql.index("note VARCHAR(255) NULL")
    assert sql.index("note VARCHAR(255) NULL") < sql.index("PRIMARY KEY (article_id, tag_id)")
    assert "PRIMARY KEY (article_id, tag_id)" in sql
    primary_key_line = next(line for line in sql.splitlines() if "PRIMARY KEY" in line)
    assert "position" not in primary_key_line
    assert "note" not in primary_key_line
    assert "idx_article_tag_position" not in sql
    assert "idx_article_tag_note" not in sql


def test_many_to_many_pivot_fields_sql_is_stable_between_calls(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    data = _m2m_doc()
    data["relations"][0]["pivot_fields"] = [
        {"name": "position", "sql_type": "INT"},
        {"name": "note", "sql_type": "VARCHAR(255)", "nullable": True},
    ]

    relations = validate_relations_definition(
        data,
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert generate_relations_sql(relations) == generate_relations_sql(relations)


def test_many_to_many_invalid_identifier_is_rejected(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    data["relations"][0]["pivot_table"] = "article tag"

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].pivot_table: doit etre un identifiant SQL valide" in str(exc_info.value)


def test_many_to_many_unknown_key_is_rejected(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc()
    data["relations"][0]["extra_key"] = "valeur_inconnue"

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(data, source="relations.json", entities_root=entities_root)

    assert "relations[0].extra_key: cle non supportee pour many_to_many" in str(exc_info.value)


def test_m2m_and_m2o_can_coexist(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    data = {
        "format_version": 1,
        "relations": [
            _valid_m2m(),
            _m2o_doc()["relations"][0],
        ],
    }

    relations = validate_relations_definition(
        data,
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert len(relations) == 2
    types = {rel.relation_type for rel in relations}
    assert types == {"many_to_many", "many_to_one"}

    sql = generate_relations_sql(relations)
    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "ALTER TABLE commande" in sql


def test_many_to_many_generates_multiple_pivot_tables(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc([
        _valid_m2m(),
        {
            "type": "many_to_many",
            "source": "article",
            "target": "category",
            "pivot_table": "article_category",
            "source_key": "article_id",
            "target_key": "category_id",
        },
    ])

    relations = validate_relations_definition(
        data,
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)

    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "CREATE TABLE IF NOT EXISTS article_category" in sql
    assert sql.index("article_tag") < sql.index("article_category")


def test_many_to_many_sql_is_stable_between_calls(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    relations = validate_relations_definition(
        _m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert generate_relations_sql(relations) == generate_relations_sql(relations)


def test_many_to_many_duplicate_pivot_table_incompatible_is_rejected(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    data = _m2m_doc([
        _valid_m2m(),
        {
            "type": "many_to_many",
            "source": "article",
            "target": "category",
            "pivot_table": "article_tag",
            "source_key": "article_id",
            "target_key": "category_id",
        },
    ])

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            data,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )

    assert "pivot_table deja utilisee avec une definition incompatible" in str(exc_info.value)


def test_many_to_many_sql_does_not_generate_crud_form_template_or_python_model(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()

    relations = validate_relations_definition(
        _m2m_doc(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)

    assert "ChoiceField" not in sql
    assert "<select" not in sql
    assert "class ArticleTag" not in sql
    assert "attach" not in sql
    assert "detach" not in sql


def test_sync_relations_writes_many_to_many_pivot_sql(tmp_path: Path):
    entities_root = tmp_path / "entities"
    entities_root.mkdir()
    (entities_root / "relations.json").write_text(
        json.dumps(_m2m_doc(), indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    output = sync_relations(entities_root)

    assert output == entities_root / "relations.sql"
    sql = output.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS article_tag" in sql
    assert "PRIMARY KEY (article_id, tag_id)" in sql
