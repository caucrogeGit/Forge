"""Garde-fou ENTITY-CONTRACT-002.

Vérifie que schemas/field.schema.json :
- existe et est un JSON valide ;
- utilise Draft 2020-12 ;
- est de type object avec additionalProperties false ;
- exige name et type dans required ;
- name référence fieldName depuis common.schema.json ;
- type est borné aux 12 types Forge autorisés (pas de file, image, etc.) ;
- decimal impose precision et scale via if/then ;
- choices est un tableau d'objets stricts (value + label) ;
- form est strict (widget, placeholder, help, readonly, hidden) ;
- crud est strict (7 booléens : list, create, edit, show, searchable, sortable, filterable).

Ce test ne fait aucune validation réseau et n'utilise pas de bibliothèque
de validation JSON Schema externe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "field.schema.json"

_ALLOWED_TYPES = frozenset({
    "string", "slug", "text", "integer", "big_integer", "float",
    "decimal", "boolean", "date", "datetime", "email", "password", "json",
})

_FORBIDDEN_TYPES = frozenset({"file", "image", "money", "uuid", "enum", "relation"})

_FORM_WIDGETS = frozenset({
    "input", "textarea", "select", "checkbox", "radio",
    "date", "datetime", "hidden", "password",
})

_CRUD_KEYS = frozenset({"list", "create", "edit", "show", "searchable", "sortable", "filterable"})


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


class TestFilePresence:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), "schemas/field.schema.json doit exister."

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
        assert schema.get("type") == "object", "Le schéma de champ doit être de type object."

    def test_additional_properties_false(self, schema):
        assert schema.get("additionalProperties") is False, (
            "additionalProperties doit être false pour interdire les clés inconnues."
        )

    def test_required_contains_name(self, schema):
        assert "name" in schema.get("required", []), "required doit contenir 'name'."

    def test_required_contains_type(self, schema):
        assert "type" in schema.get("required", []), "required doit contenir 'type'."


class TestNameProperty:
    def test_name_property_exists(self, schema):
        assert "name" in schema.get("properties", {}), "La propriété 'name' doit exister."

    def test_name_refs_common_schema(self, schema):
        ref = schema["properties"]["name"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "name.$ref doit pointer vers common.schema.json."
        )

    def test_name_refs_field_name_def(self, schema):
        ref = schema["properties"]["name"].get("$ref", "")
        assert "fieldName" in ref, (
            "name.$ref doit référencer la définition fieldName."
        )


class TestTypeProperty:
    def test_type_property_exists(self, schema):
        assert "type" in schema.get("properties", {}), "La propriété 'type' doit exister."

    @pytest.mark.parametrize("forge_type", sorted(_ALLOWED_TYPES))
    def test_allowed_type_present(self, schema, forge_type):
        enum = schema["properties"]["type"].get("enum", [])
        assert forge_type in enum, f"Le type Forge '{forge_type}' doit être dans l'enum."

    @pytest.mark.parametrize("forbidden_type", sorted(_FORBIDDEN_TYPES))
    def test_forbidden_type_absent(self, schema, forbidden_type):
        enum = schema["properties"]["type"].get("enum", [])
        assert forbidden_type not in enum, (
            f"Le type '{forbidden_type}' ne doit pas être autorisé dans ce ticket."
        )

    def test_type_enum_exact(self, schema):
        enum = set(schema["properties"]["type"].get("enum", []))
        assert enum == _ALLOWED_TYPES, (
            f"Types inattendus : {enum - _ALLOWED_TYPES} | Manquants : {_ALLOWED_TYPES - enum}."
        )


class TestDecimalConditional:
    def test_if_clause_exists(self, schema):
        assert "if" in schema, "Le schéma doit avoir une clause 'if' (contrainte decimal)."

    def test_then_clause_exists(self, schema):
        assert "then" in schema, "Le schéma doit avoir une clause 'then' (contrainte decimal)."

    def test_if_targets_decimal(self, schema):
        type_const = schema.get("if", {}).get("properties", {}).get("type", {}).get("const")
        assert type_const == "decimal", "La clause 'if' doit cibler type='decimal'."

    def test_decimal_requires_precision(self, schema):
        then_required = schema.get("then", {}).get("required", [])
        assert "precision" in then_required, "then.required doit contenir 'precision'."

    def test_decimal_requires_scale(self, schema):
        then_required = schema.get("then", {}).get("required", [])
        assert "scale" in then_required, "then.required doit contenir 'scale'."


class TestChoicesProperty:
    def test_choices_is_array(self, schema):
        choices = schema["properties"].get("choices", {})
        assert choices.get("type") == "array", "choices doit être de type array."

    def test_choices_items_is_object(self, schema):
        items = schema["properties"]["choices"].get("items", {})
        assert items.get("type") == "object", "choices.items doit être de type object."

    def test_choices_items_additional_properties_false(self, schema):
        items = schema["properties"]["choices"].get("items", {})
        assert items.get("additionalProperties") is False, (
            "choices.items doit avoir additionalProperties false."
        )

    def test_choices_items_required_value(self, schema):
        required = schema["properties"]["choices"]["items"].get("required", [])
        assert "value" in required, "choices.items.required doit contenir 'value'."

    def test_choices_items_required_label(self, schema):
        required = schema["properties"]["choices"]["items"].get("required", [])
        assert "label" in required, "choices.items.required doit contenir 'label'."

    def test_choices_label_is_string(self, schema):
        label = schema["properties"]["choices"]["items"]["properties"].get("label", {})
        assert label.get("type") == "string", "choices.items.label doit être de type string."


class TestFormProperty:
    def test_form_is_object(self, schema):
        form = schema["properties"].get("form", {})
        assert form.get("type") == "object", "form doit être de type object."

    def test_form_additional_properties_false(self, schema):
        form = schema["properties"].get("form", {})
        assert form.get("additionalProperties") is False, (
            "form doit avoir additionalProperties false."
        )

    @pytest.mark.parametrize("key", ["widget", "placeholder", "help", "readonly", "hidden"])
    def test_form_has_key(self, schema, key):
        form_props = schema["properties"]["form"].get("properties", {})
        assert key in form_props, f"form doit avoir la propriété '{key}'."

    def test_form_widget_enum_exact(self, schema):
        widget_enum = set(
            schema["properties"]["form"]["properties"]["widget"].get("enum", [])
        )
        assert widget_enum == _FORM_WIDGETS, (
            f"Widgets inattendus ou manquants : {widget_enum.symmetric_difference(_FORM_WIDGETS)}."
        )


class TestCrudProperty:
    def test_crud_is_object(self, schema):
        crud = schema["properties"].get("crud", {})
        assert crud.get("type") == "object", "crud doit être de type object."

    def test_crud_additional_properties_false(self, schema):
        crud = schema["properties"].get("crud", {})
        assert crud.get("additionalProperties") is False, (
            "crud doit avoir additionalProperties false."
        )

    @pytest.mark.parametrize("key", sorted(_CRUD_KEYS))
    def test_crud_has_key(self, schema, key):
        crud_props = schema["properties"]["crud"].get("properties", {})
        assert key in crud_props, f"crud doit avoir la propriété '{key}'."

    def test_crud_all_boolean(self, schema):
        crud_props = schema["properties"]["crud"].get("properties", {})
        for key, val in crud_props.items():
            assert val.get("type") == "boolean", f"crud.{key} doit être de type boolean."

    def test_crud_keys_exact(self, schema):
        crud_props = set(schema["properties"]["crud"].get("properties", {}).keys())
        assert crud_props == _CRUD_KEYS, (
            f"Clés crud inattendues ou manquantes : {crud_props.symmetric_difference(_CRUD_KEYS)}."
        )


class TestNumericConstraints:
    def test_max_length_minimum_1(self, schema):
        ml = schema["properties"].get("max_length", {})
        assert ml.get("minimum") == 1, "max_length.minimum doit être 1."

    def test_max_length_maximum_set(self, schema):
        ml = schema["properties"].get("max_length", {})
        assert "maximum" in ml, "max_length doit avoir une borne supérieure."

    def test_precision_minimum_1(self, schema):
        pr = schema["properties"].get("precision", {})
        assert pr.get("minimum") == 1, "precision.minimum doit être 1."

    def test_precision_maximum_65(self, schema):
        pr = schema["properties"].get("precision", {})
        assert pr.get("maximum") == 65, "precision.maximum doit être 65."

    def test_scale_minimum_0(self, schema):
        sc = schema["properties"].get("scale", {})
        assert sc.get("minimum") == 0, "scale.minimum doit être 0."

    def test_scale_maximum_30(self, schema):
        sc = schema["properties"].get("scale", {})
        assert sc.get("maximum") == 30, "scale.maximum doit être 30."
