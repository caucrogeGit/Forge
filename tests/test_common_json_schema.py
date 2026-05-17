"""Garde-fou ENTITY-CONTRACT-001.

Vérifie que schemas/common.schema.json :
- existe et est un JSON valide ;
- utilise Draft 2020-12 ;
- déclare $id et $defs ;
- contient toutes les définitions communes attendues ;
- interdit explicitement 'id' dans fieldName et relationName ;
- limite onDelete aux quatre valeurs Forge ;
- fixe schemaVersion à ['1.0'].

Ce test ne fait aucune validation réseau et n'utilise pas de bibliothèque
de validation JSON Schema externe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "common.schema.json"

_EXPECTED_DEFS = [
    "schemaVersion",
    "entityName",
    "fieldName",
    "relationName",
    "sqlIdentifier",
    "tableName",
    "columnName",
    "onDelete",
]

_EXPECTED_ON_DELETE = {"restrict", "cascade", "set_null", "no_action"}


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestFilePresence:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), "schemas/common.schema.json doit exister."

    def test_schema_file_is_valid_json(self):
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestSchemaMetadata:
    def test_draft_2020_12(self, schema):
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", (
            "$schema doit pointer vers Draft 2020-12."
        )

    def test_id_exists(self, schema):
        assert "$id" in schema, "$id doit être défini dans le schéma."

    def test_defs_exists(self, schema):
        assert "$defs" in schema, "$defs doit être défini dans le schéma."


@pytest.mark.parametrize("def_name", _EXPECTED_DEFS)
class TestDefinitionsPresent:
    def test_def_exists(self, schema, def_name):
        assert def_name in schema["$defs"], (
            f"$defs doit contenir la définition '{def_name}'."
        )


class TestFieldNameConstraints:
    def test_fieldname_forbids_id_via_not(self, schema):
        not_clause = schema["$defs"]["fieldName"].get("not")
        assert not_clause is not None, (
            "fieldName doit interdire 'id' via une clause 'not'."
        )
        assert not_clause.get("const") == "id", (
            "fieldName doit interdire explicitement la constante 'id'."
        )

    def test_fieldname_has_pattern(self, schema):
        assert "pattern" in schema["$defs"]["fieldName"], (
            "fieldName doit avoir un pattern snake_case."
        )


class TestRelationNameConstraints:
    def test_relationname_forbids_id_via_not(self, schema):
        not_clause = schema["$defs"]["relationName"].get("not")
        assert not_clause is not None, (
            "relationName doit interdire 'id' via une clause 'not'."
        )
        assert not_clause.get("const") == "id", (
            "relationName doit interdire explicitement la constante 'id'."
        )

    def test_relationname_has_pattern(self, schema):
        assert "pattern" in schema["$defs"]["relationName"], (
            "relationName doit avoir un pattern snake_case."
        )


class TestOnDeleteValues:
    def test_ondelete_enum_complete(self, schema):
        enum_vals = set(schema["$defs"]["onDelete"].get("enum", []))
        for expected in _EXPECTED_ON_DELETE:
            assert expected in enum_vals, (
                f"onDelete doit contenir '{expected}'."
            )

    def test_ondelete_enum_exact(self, schema):
        enum_vals = set(schema["$defs"]["onDelete"].get("enum", []))
        assert enum_vals == _EXPECTED_ON_DELETE, (
            f"onDelete contient des valeurs inattendues : {enum_vals - _EXPECTED_ON_DELETE}."
        )


class TestSchemaVersionConstraint:
    def test_schema_version_enum(self, schema):
        sv = schema["$defs"]["schemaVersion"]
        assert sv.get("enum") == ["1.0"], (
            "schemaVersion doit avoir enum=['1.0']."
        )

    def test_schema_version_type_string(self, schema):
        sv = schema["$defs"]["schemaVersion"]
        assert sv.get("type") == "string", (
            "schemaVersion doit être de type string."
        )


class TestSqlIdentifierDefs:
    def test_tablename_refs_sql_identifier(self, schema):
        table = schema["$defs"]["tableName"]
        assert "$ref" in table, (
            "tableName doit utiliser $ref vers sqlIdentifier."
        )
        assert "sqlIdentifier" in table["$ref"], (
            "tableName.$ref doit pointer vers #/$defs/sqlIdentifier."
        )

    def test_columnname_refs_sql_identifier(self, schema):
        col = schema["$defs"]["columnName"]
        assert "$ref" in col, (
            "columnName doit utiliser $ref vers sqlIdentifier."
        )
        assert "sqlIdentifier" in col["$ref"], (
            "columnName.$ref doit pointer vers #/$defs/sqlIdentifier."
        )

    def test_sql_identifier_has_pattern(self, schema):
        assert "pattern" in schema["$defs"]["sqlIdentifier"], (
            "sqlIdentifier doit avoir un pattern pour valider le format snake_case SQL."
        )
