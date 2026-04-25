import json
from pathlib import Path

import pytest

from forge_cli.entities.relations import (
    EntityRelationsError,
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


def _relations_json() -> dict:
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
    assert sql == (
        "ALTER TABLE commande\n"
        "    ADD CONSTRAINT fk_commande_contact\n"
        "    FOREIGN KEY (ContactId)\n"
        "    REFERENCES contact (Id)\n"
        "    ON DELETE RESTRICT\n"
        "    ON UPDATE CASCADE;\n"
    )


def test_collects_multiple_relation_errors(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    invalid = {
        "format_version": 1,
        "relations": [
            {
                "name": "commande contact",
                "type": "one_to_one",
                "from_entity": "commande",
                "to_entity": "Contact",
                "from_field": "inconnu",
                "to_field": "id",
                "foreign_key_name": "fk commande",
                "on_delete": "SET NULL",
                "on_update": "INVALID",
            },
            {
                "name": "commande contact",
                "type": "many_to_one",
                "from_entity": "Commande",
                "to_entity": "Contact",
                "from_field": "contact_id",
                "to_field": "id",
                "foreign_key_name": "fk commande",
                "on_delete": "RESTRICT",
                "on_update": "CASCADE",
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
    assert "relations[0].name: doit etre un identifiant valide" in message
    assert "relations[0].type: doit valoir 'many_to_one' en V1" in message
    assert "relations[0].from_entity: doit etre un nom d'entite PascalCase valide" in message
    assert "relations[0].foreign_key_name: doit etre un identifiant SQL valide" in message
    assert "relations[0].on_update: doit etre l'une des valeurs SQL supportees en V1" in message
    assert "relations[0]: l'entite 'commande' est introuvable" in message
    assert "relations[1].name: doit etre unique" in message
    assert "relations[1].foreign_key_name: doit etre unique" in message


def test_set_null_requires_nullable_from_field(tmp_path: Path):
    entities_root = tmp_path / "entities"
    _write_entity(entities_root, "Contact", _contact_entity())
    _write_entity(entities_root, "Commande", _commande_entity())

    invalid = _relations_json()
    invalid["relations"][0]["on_delete"] = "SET NULL"

    with pytest.raises(EntityRelationsError, match="SET NULL requiert un from_field nullable"):
        validate_relations_definition(
            invalid,
            source=str(entities_root / "relations.json"),
            entities_root=entities_root,
        )
