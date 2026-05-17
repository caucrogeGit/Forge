"""Garde-fou ENTITY-CONTRACT-003.

Vérifie que schemas/entity.schema.json :
- existe et est un JSON valide ;
- utilise Draft 2020-12 ;
- est de type object avec additionalProperties false ;
- exige schema_version, name, table, fields ;
- déclare uniquement les propriétés autorisées ;
- schema_version référence common.schema.json#/$defs/schemaVersion ;
- name référence common.schema.json#/$defs/entityName ;
- table référence common.schema.json#/$defs/tableName ;
- fields est un tableau dont les items référencent field.schema.json ;
- indexes est un tableau avec name/fields/unique stricts ;
- index.name référence common.schema.json#/$defs/sqlIdentifier ;
- index.fields.items référence common.schema.json#/$defs/fieldName ;
- options est strict (timestamps, soft_delete booléens) ;
- aucune propriété relationnelle ou runtime n'est déclarée.

Ce test ne fait aucune validation réseau et n'utilise pas de bibliothèque
de validation JSON Schema externe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "entity.schema.json"

_EXPECTED_PROPERTIES = frozenset({
    "$schema", "schema_version", "name", "table",
    "label", "plural_label", "description",
    "fields", "indexes", "options",
})

_REQUIRED_FIELDS = frozenset({"schema_version", "name", "table", "fields"})

_FORBIDDEN_RELATIONAL = frozenset({
    "relations", "many_to_one", "many_to_many", "pivot",
})

_FORBIDDEN_RUNTIME = frozenset({
    "controller", "model", "route", "crud_controller",
})

_OPTIONS_KEYS = frozenset({"timestamps", "soft_delete"})

_INDEX_REQUIRED = frozenset({"name", "fields"})


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestFilePresence:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), "schemas/entity.schema.json doit exister."

    def test_schema_file_is_valid_json(self):
        json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestSchemaMetadata:
    def test_draft_2020_12(self, schema):
        assert schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema", (
            "$schema doit pointer vers Draft 2020-12."
        )

    def test_id_exists(self, schema):
        assert "$id" in schema, "$id doit être défini."

    def test_type_is_object(self, schema):
        assert schema.get("type") == "object", "Le schéma d'entité doit être de type object."

    def test_additional_properties_false(self, schema):
        assert schema.get("additionalProperties") is False, (
            "additionalProperties doit être false pour interdire les clés inconnues."
        )


class TestRequiredFields:
    @pytest.mark.parametrize("field", sorted(_REQUIRED_FIELDS))
    def test_required_contains_field(self, schema, field):
        assert field in schema.get("required", []), (
            f"required doit contenir '{field}'."
        )

    def test_required_exact(self, schema):
        required = set(schema.get("required", []))
        assert required == _REQUIRED_FIELDS, (
            f"required contient des champs inattendus ou manquants : "
            f"inattendus={required - _REQUIRED_FIELDS}, manquants={_REQUIRED_FIELDS - required}."
        )


class TestAllowedProperties:
    def test_only_expected_properties_declared(self, schema):
        props = set(schema.get("properties", {}).keys())
        unexpected = props - _EXPECTED_PROPERTIES
        assert not unexpected, (
            f"Propriétés inattendues dans le schéma : {unexpected}."
        )

    def test_all_expected_properties_declared(self, schema):
        props = set(schema.get("properties", {}).keys())
        missing = _EXPECTED_PROPERTIES - props
        assert not missing, (
            f"Propriétés attendues manquantes : {missing}."
        )


class TestCommonRefs:
    def test_schema_version_refs_common(self, schema):
        ref = schema["properties"]["schema_version"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "schema_version doit référencer common.schema.json."
        )
        assert "schemaVersion" in ref, (
            "schema_version doit référencer $defs/schemaVersion."
        )

    def test_name_refs_entity_name(self, schema):
        ref = schema["properties"]["name"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "name doit référencer common.schema.json."
        )
        assert "entityName" in ref, (
            "name doit référencer $defs/entityName."
        )

    def test_table_refs_table_name(self, schema):
        ref = schema["properties"]["table"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "table doit référencer common.schema.json."
        )
        assert "tableName" in ref, (
            "table doit référencer $defs/tableName."
        )


class TestFieldsProperty:
    def test_fields_is_array(self, schema):
        fields = schema["properties"].get("fields", {})
        assert fields.get("type") == "array", "fields doit être de type array."

    def test_fields_items_ref_field_schema(self, schema):
        items = schema["properties"]["fields"].get("items", {})
        ref = items.get("$ref", "")
        assert "field.schema.json" in ref, (
            "fields.items doit référencer field.schema.json."
        )

    def test_fields_min_items_1(self, schema):
        fields = schema["properties"].get("fields", {})
        assert fields.get("minItems") == 1, (
            "fields doit exiger au moins 1 champ (minItems: 1)."
        )


class TestIndexesProperty:
    def test_indexes_is_array(self, schema):
        indexes = schema["properties"].get("indexes", {})
        assert indexes.get("type") == "array", "indexes doit être de type array."

    def test_indexes_items_is_object(self, schema):
        items = schema["properties"]["indexes"].get("items", {})
        assert items.get("type") == "object", "indexes.items doit être de type object."

    def test_indexes_items_additional_properties_false(self, schema):
        items = schema["properties"]["indexes"].get("items", {})
        assert items.get("additionalProperties") is False, (
            "indexes.items doit avoir additionalProperties false."
        )

    @pytest.mark.parametrize("key", sorted(_INDEX_REQUIRED))
    def test_indexes_items_required_contains(self, schema, key):
        required = schema["properties"]["indexes"]["items"].get("required", [])
        assert key in required, f"indexes.items.required doit contenir '{key}'."

    def test_index_name_refs_sql_identifier(self, schema):
        index_name = schema["properties"]["indexes"]["items"]["properties"].get("name", {})
        ref = index_name.get("$ref", "")
        assert "common.schema.json" in ref, (
            "indexes.items.name doit référencer common.schema.json."
        )
        assert "sqlIdentifier" in ref, (
            "indexes.items.name doit référencer $defs/sqlIdentifier."
        )

    def test_index_fields_is_array(self, schema):
        index_fields = schema["properties"]["indexes"]["items"]["properties"].get("fields", {})
        assert index_fields.get("type") == "array", (
            "indexes.items.fields doit être de type array."
        )

    def test_index_fields_items_ref_field_name(self, schema):
        index_fields = schema["properties"]["indexes"]["items"]["properties"]["fields"]
        items_ref = index_fields.get("items", {}).get("$ref", "")
        assert "common.schema.json" in items_ref, (
            "indexes.items.fields.items doit référencer common.schema.json."
        )
        assert "fieldName" in items_ref, (
            "indexes.items.fields.items doit référencer $defs/fieldName."
        )

    def test_index_fields_min_items_1(self, schema):
        index_fields = schema["properties"]["indexes"]["items"]["properties"].get("fields", {})
        assert index_fields.get("minItems") == 1, (
            "indexes.items.fields doit exiger au moins 1 élément."
        )

    def test_index_unique_is_boolean(self, schema):
        unique = schema["properties"]["indexes"]["items"]["properties"].get("unique", {})
        assert unique.get("type") == "boolean", (
            "indexes.items.unique doit être de type boolean."
        )


class TestOptionsProperty:
    def test_options_is_object(self, schema):
        options = schema["properties"].get("options", {})
        assert options.get("type") == "object", "options doit être de type object."

    def test_options_additional_properties_false(self, schema):
        options = schema["properties"].get("options", {})
        assert options.get("additionalProperties") is False, (
            "options doit avoir additionalProperties false."
        )

    def test_options_timestamps_is_boolean(self, schema):
        ts = schema["properties"]["options"]["properties"].get("timestamps", {})
        assert ts.get("type") == "boolean", "options.timestamps doit être de type boolean."

    def test_options_soft_delete_is_boolean(self, schema):
        sd = schema["properties"]["options"]["properties"].get("soft_delete", {})
        assert sd.get("type") == "boolean", "options.soft_delete doit être de type boolean."

    def test_options_keys_exact(self, schema):
        keys = set(schema["properties"]["options"].get("properties", {}).keys())
        assert keys == _OPTIONS_KEYS, (
            f"options doit avoir exactement {_OPTIONS_KEYS} — trouvé : {keys}."
        )


class TestForbiddenProperties:
    @pytest.mark.parametrize("prop", sorted(_FORBIDDEN_RELATIONAL))
    def test_no_relational_property(self, schema, prop):
        props = schema.get("properties", {})
        assert prop not in props, (
            f"La propriété relationnelle '{prop}' ne doit pas être dans entity.schema.json "
            f"(réservée à relations.schema.json)."
        )

    @pytest.mark.parametrize("prop", sorted(_FORBIDDEN_RUNTIME))
    def test_no_runtime_property(self, schema, prop):
        props = schema.get("properties", {})
        assert prop not in props, (
            f"La propriété runtime '{prop}' ne doit pas être dans entity.schema.json."
        )
