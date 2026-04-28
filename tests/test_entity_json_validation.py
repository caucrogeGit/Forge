import pytest

from forge_cli.entities.validation import (
    EntityDefinitionError,
    normalize_entity_definition,
    validate_entity_definition,
)


def valid_entity() -> dict:
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
            },
            {
                "name": "nom",
                "column": "Nom",
                "python_type": "str",
                "sql_type": "VARCHAR(100)",
                "nullable": False,
                "primary_key": False,
                "auto_increment": False,
                "constraints": {"not_empty": True, "max_length": 100},
            },
        ],
    }


def test_valid_entity_definition_passes():
    validate_entity_definition(valid_entity(), source="contact.json")


def test_collects_multiple_errors():
    data = valid_entity()
    data["entity"] = "contact"
    data["fields"][0]["nullable"] = True
    data["fields"][1]["column"] = "Id"

    with pytest.raises(EntityDefinitionError) as exc_info:
        validate_entity_definition(data, source="contact.json")

    message = str(exc_info.value)
    assert "entity: doit etre un nom PascalCase valide" in message
    assert "fields[0].nullable: une cle primaire ne peut pas etre nullable" in message
    assert "fields[1].column: doit etre unique" in message


def test_reserved_sql_words_are_rejected_for_entity_table_and_column():
    data = valid_entity()
    data["entity"] = "User"
    data["table"] = "order"
    data["fields"][1]["column"] = "Group"

    with pytest.raises(EntityDefinitionError) as exc_info:
        validate_entity_definition(data, source="contact.json")

    message = str(exc_info.value)
    assert "entity: ne doit pas etre un mot reserve SQL/MariaDB" in message
    assert "table: ne doit pas etre un mot reserve SQL/MariaDB" in message
    assert "fields[1].column: ne doit pas etre un mot reserve SQL/MariaDB" in message


def test_short_author_format_is_normalized_with_defaults():
    data = {
        "entity": "Contact",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            },
            {
                "name": "date_naissance",
                "sql_type": "DATE",
            },
        ],
    }

    normalized = normalize_entity_definition(data, source="contact.json")

    assert normalized["format_version"] == 1
    assert normalized["table"] == "contact"
    assert normalized["description"] == ""
    assert normalized["fields"][0]["column"] == "Id"
    assert normalized["fields"][0]["python_type"] == "int"
    assert normalized["fields"][0]["nullable"] is False
    assert normalized["fields"][0]["constraints"] == {}
    assert normalized["fields"][1]["column"] == "DateNaissance"
    assert normalized["fields"][1]["python_type"] == "date"
    assert normalized["fields"][1]["primary_key"] is False
    assert normalized["fields"][1]["auto_increment"] is False


def test_verbose_legacy_format_still_passes_and_is_preserved():
    normalized = normalize_entity_definition(valid_entity(), source="contact.json")

    assert normalized["format_version"] == 1
    assert normalized["table"] == "contact"
    assert normalized["fields"][0]["column"] == "Id"
    assert normalized["fields"][0]["python_type"] == "int"
    assert normalized["fields"][1]["constraints"] == {"not_empty": True, "max_length": 100}


def test_mixed_short_and_verbose_fields_are_supported():
    data = {
        "entity": "CommandeClient",
        "description": "Mixte",
        "fields": [
            {
                "name": "id",
                "sql_type": "INT",
                "primary_key": True,
                "auto_increment": True,
            },
            {
                "name": "montant_ttc",
                "column": "MontantTTC",
                "python_type": "float",
                "sql_type": "DECIMAL(10,2)",
                "constraints": {"min_value": 0},
            },
        ],
    }

    normalized = normalize_entity_definition(data, source="commande_client.json")

    assert normalized["table"] == "commande_client"
    assert normalized["description"] == "Mixte"
    assert normalized["fields"][0]["column"] == "Id"
    assert normalized["fields"][1]["column"] == "MontantTTC"
    assert normalized["fields"][1]["python_type"] == "float"
    assert normalized["fields"][1]["constraints"] == {"min_value": 0}


def test_missing_python_type_fails_when_sql_type_cannot_be_inferred():
    data = {
        "entity": "Contact",
        "fields": [
            {
                "name": "id",
                "sql_type": "JSON",
                "primary_key": True,
            }
        ],
    }

    with pytest.raises(EntityDefinitionError, match="python_type: absent et impossible a deduire depuis sql_type"):
        normalize_entity_definition(data, source="contact.json")


def test_default_null_requires_nullable():
    data = valid_entity()
    data["fields"][1]["default"] = None

    with pytest.raises(EntityDefinitionError, match="null n'est autorise que si nullable vaut true"):
        validate_entity_definition(data, source="contact.json")


def test_constraint_type_must_match_python_type():
    data = valid_entity()
    data["fields"][0]["constraints"] = {"max_length": 10}

    with pytest.raises(EntityDefinitionError, match="est reserve aux champs de type str"):
        validate_entity_definition(data, source="contact.json")


def test_auto_increment_requires_integer_primary_key():
    data = valid_entity()
    data["fields"][0]["python_type"] = "str"
    data["fields"][0]["sql_type"] = "VARCHAR(20)"

    with pytest.raises(EntityDefinitionError) as exc_info:
        validate_entity_definition(data, source="contact.json")

    message = str(exc_info.value)
    assert "requiert python_type='int'" in message
    assert "requiert un sql_type entier compatible" in message


def test_bool_requires_bool_or_boolean_sql_type():
    data = valid_entity()
    data["fields"].append(
        {
            "name": "actif",
            "column": "Actif",
            "python_type": "bool",
            "sql_type": "TINYINT(1)",
            "nullable": False,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
        }
    )

    with pytest.raises(EntityDefinitionError, match="n'est pas compatible avec python_type='bool'"):
        validate_entity_definition(data, source="contact.json")


def test_bool_accepts_boolean_sql_type():
    data = valid_entity()
    data["fields"].append(
        {
            "name": "actif",
            "column": "Actif",
            "python_type": "bool",
            "sql_type": "BOOLEAN",
            "nullable": False,
            "primary_key": False,
            "auto_increment": False,
            "constraints": {},
        }
    )

    validate_entity_definition(data, source="contact.json")


def test_date_and_datetime_types_are_accepted_with_compatible_sql_types():
    data = valid_entity()
    data["fields"].append(
        {
            "name": "date_naissance",
            "column": "DateNaissance",
            "python_type": "date",
            "sql_type": "DATE",
            "nullable": True,
            "primary_key": False,
            "auto_increment": False,
            "default": "2026-04-23",
            "constraints": {},
        }
    )
    data["fields"].append(
        {
            "name": "cree_le",
            "column": "CreeLe",
            "python_type": "datetime",
            "sql_type": "TIMESTAMP",
            "nullable": True,
            "primary_key": False,
            "auto_increment": False,
            "default": "2026-04-23T10:15:30",
            "constraints": {},
        }
    )

    validate_entity_definition(data, source="contact.json")


def test_date_and_datetime_defaults_must_be_iso_strings():
    data = valid_entity()
    data["fields"].append(
        {
            "name": "date_naissance",
            "column": "DateNaissance",
            "python_type": "date",
            "sql_type": "DATE",
            "nullable": True,
            "primary_key": False,
            "auto_increment": False,
            "default": "23/04/2026",
            "constraints": {},
        }
    )
    data["fields"].append(
        {
            "name": "cree_le",
            "column": "CreeLe",
            "python_type": "datetime",
            "sql_type": "DATETIME",
            "nullable": True,
            "primary_key": False,
            "auto_increment": False,
            "default": "23/04/2026 10:15",
            "constraints": {},
        }
    )

    with pytest.raises(EntityDefinitionError) as exc_info:
        validate_entity_definition(data, source="contact.json")

    message = str(exc_info.value)
    assert "python_type='date'" in message
    assert "python_type='datetime'" in message
