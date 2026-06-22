import json
from pathlib import Path

import pytest

from cli.entities.relations import (
    EntityRelationsError,
    ValidatedRelation,
    generate_relations_sql,
    validate_relations_definition,
)


def _write_entity(root: Path, name: str, data: dict) -> None:
    entity_dir = root / name.lower()
    entity_dir.mkdir(parents=True, exist_ok=True)
    (entity_dir / f"{name.lower()}.json").write_text(
        json.dumps(data, indent=2, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )


def _contact_entity(sql_type: str = "INT") -> dict:
    return {
        "entity": "Contact",
        "table": "contact",
        "description": "",
        "fields": [
            {
                "name": "id",
                "column": "id",
                "python_type": "int",
                "sql_type": sql_type,
                "nullable": False,
                "primary_key": True,
                "auto_increment": True,
                "constraints": {},
            }
        ],
    }


def _commande_entity(contact_sql_type: str = "INT") -> dict:
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
                "sql_type": contact_sql_type,
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {},
            },
        ],
    }


def _relations_json() -> dict:
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
                "index": True,
            }
        ],
    }


def test_validate_relations_and_generate_sql(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    relations = validate_relations_definition(
        _relations_json(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    sql = generate_relations_sql(relations)
    assert "ALTER TABLE commande" in sql
    assert "FOREIGN KEY (contact_id)" in sql
    assert "REFERENCES contact" in sql
    assert "ON DELETE RESTRICT" in sql


def test_canonical_m2o_returns_validated_relation(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    relations = validate_relations_definition(
        _relations_json(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert len(relations) == 1
    assert isinstance(relations[0], ValidatedRelation)
    assert relations[0].relation_type == "many_to_one"
    assert relations[0].from_entity == "Commande"
    assert relations[0].to_entity == "Contact"


def test_collects_multiple_relation_errors(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    invalid = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Commande",
                "to": "Contact",
                "name": "contact",
                "foreign_key": "contact_id",
                "on_delete": "restrict",
            },
            {
                "type": "many_to_one",
                "from": "Commande",
                "to": "Contact",
                "name": "contact",  # duplicate name
                "foreign_key": "contact_id",  # duplicate FK
                "on_delete": "restrict",
            },
        ],
    }

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            invalid,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )

    message = str(exc_info.value)
    assert "relations[1].name: doit etre unique" in message
    assert "relations[1].foreign_key: doit etre unique" in message


def test_set_null_requires_nullable_from_field(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    invalid = {
        "schema_version": "1.0",
        "relations": [
            {
                "type": "many_to_one",
                "from": "Commande",
                "to": "Contact",
                "name": "contact",
                "foreign_key": "contact_id",
                "nullable": False,
                "on_delete": "set_null",  # contact_id is not nullable
                "index": True,
            }
        ],
    }

    with pytest.raises(EntityRelationsError, match="SET NULL requiert un from_field nullable"):
        validate_relations_definition(
            invalid,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )


def test_relation_int_to_int_is_accepted(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity("INT"))
    _write_entity(entities_root, "Commande", _commande_entity("INT"))

    relations = validate_relations_definition(
        _relations_json(),
        source=str(entities_root / "relations.json"),
        entities_root=entities_root,
    )

    assert len(relations) == 1


def test_format_version_1_relations_are_rejected(tmp_path: Path):
    """Un relations.json avec format_version: 1 est refusé avec un message clair."""
    entities_root = tmp_path / "entities"
    entities_root.mkdir(parents=True)

    legacy_doc = {
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

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            legacy_doc,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )

    assert "format_version" in str(exc_info.value)
    assert 'schema_version' in str(exc_info.value)


def test_format_version_rejection_does_not_mention_field_errors(tmp_path: Path):
    """Quand format_version: 1 est présent, l'erreur porte sur le format, pas les champs."""
    entities_root = tmp_path / "entities"
    entities_root.mkdir(parents=True)

    legacy_doc = {"format_version": 1, "relations": []}

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            legacy_doc,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )

    assert "format_version" in str(exc_info.value)


def test_legacy_m2o_keys_from_entity_is_rejected(tmp_path: Path):
    """Une relation avec from_entity au lieu de from est refusée."""
    entities_root = tmp_path / "entities"
    entities_root.mkdir(parents=True)

    doc = {
        "schema_version": "1.0",
        "relations": [
            {
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

    with pytest.raises(EntityRelationsError) as exc_info:
        validate_relations_definition(
            doc,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )

    assert "legacy" in str(exc_info.value).lower() or "from" in str(exc_info.value)
