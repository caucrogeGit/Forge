"""Garde-fou ENTITY-CONTRACT-004.

Vérifie que schemas/pivot.schema.json :
- existe et est un JSON valide ;
- utilise Draft 2020-12 ;
- est de type object avec additionalProperties false ;
- exige table, from_key, to_key, id, unique_pair dans required ;
- required est exactement ces 5 clés ;
- table référence common.schema.json#/$defs/tableName ;
- from_key référence common.schema.json#/$defs/columnName ;
- to_key référence common.schema.json#/$defs/columnName ;
- id est const true (id technique AUTO_INCREMENT) ;
- unique_pair est const true (contrainte UNIQUE sur la paire) ;
- on_delete référence common.schema.json#/$defs/onDelete ;
- fields est un tableau dont les items référencent field.schema.json ;
- aucune propriété de clé primaire composite n'est déclarée ;
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
# pivot.schema.json est hors cœur (ADR-057), embarqué par forge-mvc-entities
# qui a absorbé pivot (ADR-070).
SCHEMA_PATH = (
    PROJECT_ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities"
    / "schemas" / "pivot.schema.json"
)

_REQUIRED_FIELDS = frozenset({"table", "from_key", "to_key", "id", "unique_pair"})

_EXPECTED_PROPERTIES = frozenset({
    "table", "from_key", "to_key", "id", "unique_pair", "on_delete", "fields",
})

_FORBIDDEN_COMPOSITE_PK = frozenset({
    "primary_key", "composite_pk", "compound_key",
})

_FORBIDDEN_RELATIONAL = frozenset({
    "relations", "many_to_one", "many_to_many",
})

_FORBIDDEN_RUNTIME = frozenset({
    "controller", "model", "route", "crud_controller",
})


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestFilePresence:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), "schemas/pivot.schema.json doit exister."

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
        assert schema.get("type") == "object", "Le schéma pivot doit être de type object."

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
            f"Propriétés inattendues dans le schéma pivot : {unexpected}."
        )

    def test_all_expected_properties_declared(self, schema):
        props = set(schema.get("properties", {}).keys())
        missing = _EXPECTED_PROPERTIES - props
        assert not missing, (
            f"Propriétés attendues manquantes : {missing}."
        )


class TestCommonRefs:
    def test_table_refs_table_name(self, schema):
        ref = schema["properties"]["table"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "table doit référencer common.schema.json."
        )
        assert "tableName" in ref, (
            "table doit référencer $defs/tableName."
        )

    def test_from_key_refs_column_name(self, schema):
        ref = schema["properties"]["from_key"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "from_key doit référencer common.schema.json."
        )
        assert "columnName" in ref, (
            "from_key doit référencer $defs/columnName."
        )

    def test_to_key_refs_column_name(self, schema):
        ref = schema["properties"]["to_key"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "to_key doit référencer common.schema.json."
        )
        assert "columnName" in ref, (
            "to_key doit référencer $defs/columnName."
        )

    def test_on_delete_refs_on_delete(self, schema):
        ref = schema["properties"]["on_delete"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "on_delete doit référencer common.schema.json."
        )
        assert "onDelete" in ref, (
            "on_delete doit référencer $defs/onDelete."
        )


class TestIdProperty:
    def test_id_is_const_true(self, schema):
        id_prop = schema["properties"].get("id", {})
        assert id_prop.get("const") is True, (
            "id doit être const: true (id technique AUTO_INCREMENT obligatoire)."
        )

    def test_id_has_no_type(self, schema):
        id_prop = schema["properties"].get("id", {})
        assert "type" not in id_prop, (
            "id ne doit pas avoir de 'type' explicite — const suffit."
        )


class TestUniquePairProperty:
    def test_unique_pair_is_const_true(self, schema):
        up = schema["properties"].get("unique_pair", {})
        assert up.get("const") is True, (
            "unique_pair doit être const: true (contrainte UNIQUE sur la paire obligatoire)."
        )

    def test_unique_pair_has_no_type(self, schema):
        up = schema["properties"].get("unique_pair", {})
        assert "type" not in up, (
            "unique_pair ne doit pas avoir de 'type' explicite — const suffit."
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

    def test_fields_has_no_min_items(self, schema):
        fields = schema["properties"].get("fields", {})
        assert "minItems" not in fields, (
            "fields ne doit pas avoir minItems — les attributs pivot sont optionnels."
        )


class TestForbiddenProperties:
    @pytest.mark.parametrize("prop", sorted(_FORBIDDEN_COMPOSITE_PK))
    def test_no_composite_pk_property(self, schema, prop):
        props = schema.get("properties", {})
        assert prop not in props, (
            f"La propriété '{prop}' ne doit pas être dans pivot.schema.json "
            f"(Forge 1.x utilise un id technique, pas de clé primaire composite)."
        )

    @pytest.mark.parametrize("prop", sorted(_FORBIDDEN_RELATIONAL))
    def test_no_relational_property(self, schema, prop):
        props = schema.get("properties", {})
        assert prop not in props, (
            f"La propriété relationnelle '{prop}' ne doit pas être dans pivot.schema.json."
        )

    @pytest.mark.parametrize("prop", sorted(_FORBIDDEN_RUNTIME))
    def test_no_runtime_property(self, schema, prop):
        props = schema.get("properties", {})
        assert prop not in props, (
            f"La propriété runtime '{prop}' ne doit pas être dans pivot.schema.json."
        )
