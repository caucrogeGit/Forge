"""Garde-fou ENTITY-CONTRACT-005.

Vérifie que schemas/relations.schema.json :
- existe et est un JSON valide ;
- utilise Draft 2020-12 ;
- est de type object avec additionalProperties false ;
- exige schema_version et relations dans required ;
- déclare uniquement les propriétés racine attendues ;
- schema_version référence common.schema.json#/$defs/schemaVersion ;
- relations est un tableau dont les items utilisent oneOf ;
- oneOf référence manyToOne et manyToMany depuis $defs ;
- manyToOne a additionalProperties false, required exact, type const, refs corrects ;
- manyToMany a additionalProperties false, required exact, type const, refs corrects ;
- manyToMany.pivot référence pivot.schema.json ;
- manyToMany ne porte pas from_key, to_key, id, unique_pair directement ;
- one_to_one, polymorphic, has_many, belongs_to absents de $defs ;
- propriétés runtime absentes du schéma.

Ce test ne fait aucune validation réseau et n'utilise pas de bibliothèque
de validation JSON Schema externe.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = PROJECT_ROOT / "schemas" / "relations.schema.json"

_EXPECTED_ROOT_PROPERTIES = frozenset({"$schema", "schema_version", "relations"})
_REQUIRED_ROOT = frozenset({"schema_version", "relations"})

_M2O_REQUIRED = frozenset({"type", "from", "to", "name"})
_M2M_REQUIRED = frozenset({"type", "from", "to", "name", "pivot"})

_M2O_EXPECTED_PROPS = frozenset({
    "type", "from", "to", "name", "inverse_name",
    "foreign_key", "nullable", "on_delete", "index",
})

_M2M_EXPECTED_PROPS = frozenset({
    "type", "from", "to", "name", "inverse_name", "pivot",
})

_M2M_FORBIDDEN_DIRECT = frozenset({"from_key", "to_key", "id", "unique_pair"})

_FORBIDDEN_RELATION_TYPES = frozenset({"one_to_one", "polymorphic", "has_many", "belongs_to"})

_FORBIDDEN_RUNTIME = frozenset({"controller", "model", "route", "crud_controller", "sql", "migration"})


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def m2o(schema) -> dict:
    return schema["$defs"]["manyToOne"]


@pytest.fixture(scope="module")
def m2m(schema) -> dict:
    return schema["$defs"]["manyToMany"]


class TestFilePresence:
    def test_schema_file_exists(self):
        assert SCHEMA_PATH.exists(), "schemas/relations.schema.json doit exister."

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
        assert schema.get("type") == "object", "Le schéma relations doit être de type object."

    def test_additional_properties_false(self, schema):
        assert schema.get("additionalProperties") is False, (
            "additionalProperties doit être false pour interdire les clés inconnues."
        )


class TestRequiredRoot:
    @pytest.mark.parametrize("field", sorted(_REQUIRED_ROOT))
    def test_required_contains_field(self, schema, field):
        assert field in schema.get("required", []), (
            f"required doit contenir '{field}'."
        )

    def test_required_exact(self, schema):
        required = set(schema.get("required", []))
        assert required == _REQUIRED_ROOT, (
            f"required racine contient des champs inattendus ou manquants : "
            f"inattendus={required - _REQUIRED_ROOT}, manquants={_REQUIRED_ROOT - required}."
        )


class TestRootProperties:
    def test_only_expected_root_properties(self, schema):
        props = set(schema.get("properties", {}).keys())
        unexpected = props - _EXPECTED_ROOT_PROPERTIES
        assert not unexpected, (
            f"Propriétés racine inattendues : {unexpected}."
        )

    def test_all_expected_root_properties_declared(self, schema):
        props = set(schema.get("properties", {}).keys())
        missing = _EXPECTED_ROOT_PROPERTIES - props
        assert not missing, (
            f"Propriétés racine manquantes : {missing}."
        )

    def test_schema_version_refs_common(self, schema):
        ref = schema["properties"]["schema_version"].get("$ref", "")
        assert "common.schema.json" in ref, (
            "schema_version doit référencer common.schema.json."
        )
        assert "schemaVersion" in ref, (
            "schema_version doit référencer $defs/schemaVersion."
        )


class TestRelationsProperty:
    def test_relations_is_array(self, schema):
        rel = schema["properties"].get("relations", {})
        assert rel.get("type") == "array", "relations doit être de type array."

    def test_relations_items_uses_one_of(self, schema):
        items = schema["properties"]["relations"].get("items", {})
        assert "oneOf" in items, "relations.items doit utiliser oneOf."

    def test_relations_one_of_has_two_entries(self, schema):
        one_of = schema["properties"]["relations"]["items"].get("oneOf", [])
        assert len(one_of) == 2, "relations.items.oneOf doit avoir exactement 2 entrées."

    def test_relations_one_of_refs_many_to_one(self, schema):
        one_of = schema["properties"]["relations"]["items"]["oneOf"]
        refs = [entry.get("$ref", "") for entry in one_of]
        assert any("manyToOne" in r for r in refs), (
            "relations.items.oneOf doit référencer #/$defs/manyToOne."
        )

    def test_relations_one_of_refs_many_to_many(self, schema):
        one_of = schema["properties"]["relations"]["items"]["oneOf"]
        refs = [entry.get("$ref", "") for entry in one_of]
        assert any("manyToMany" in r for r in refs), (
            "relations.items.oneOf doit référencer #/$defs/manyToMany."
        )


class TestDefsPresence:
    def test_defs_exists(self, schema):
        assert "$defs" in schema, "Le schéma doit définir $defs."

    def test_many_to_one_def_exists(self, schema):
        assert "manyToOne" in schema.get("$defs", {}), "$defs doit contenir manyToOne."

    def test_many_to_many_def_exists(self, schema):
        assert "manyToMany" in schema.get("$defs", {}), "$defs doit contenir manyToMany."


class TestManyToOne:
    def test_m2o_type_is_object(self, m2o):
        assert m2o.get("type") == "object", "manyToOne doit être de type object."

    def test_m2o_additional_properties_false(self, m2o):
        assert m2o.get("additionalProperties") is False, (
            "manyToOne doit avoir additionalProperties false."
        )

    @pytest.mark.parametrize("field", sorted(_M2O_REQUIRED))
    def test_m2o_required_contains(self, m2o, field):
        assert field in m2o.get("required", []), (
            f"manyToOne.required doit contenir '{field}'."
        )

    def test_m2o_required_exact(self, m2o):
        required = set(m2o.get("required", []))
        assert required == _M2O_REQUIRED, (
            f"manyToOne.required contient des champs inattendus ou manquants : "
            f"inattendus={required - _M2O_REQUIRED}, manquants={_M2O_REQUIRED - required}."
        )

    def test_m2o_type_is_const_many_to_one(self, m2o):
        assert m2o["properties"]["type"].get("const") == "many_to_one", (
            "manyToOne.type doit être const 'many_to_one'."
        )

    def test_m2o_from_refs_entity_name(self, m2o):
        ref = m2o["properties"]["from"].get("$ref", "")
        assert "common.schema.json" in ref and "entityName" in ref, (
            "manyToOne.from doit référencer common.schema.json#/$defs/entityName."
        )

    def test_m2o_to_refs_entity_name(self, m2o):
        ref = m2o["properties"]["to"].get("$ref", "")
        assert "common.schema.json" in ref and "entityName" in ref, (
            "manyToOne.to doit référencer common.schema.json#/$defs/entityName."
        )

    def test_m2o_name_refs_relation_name(self, m2o):
        ref = m2o["properties"]["name"].get("$ref", "")
        assert "common.schema.json" in ref and "relationName" in ref, (
            "manyToOne.name doit référencer common.schema.json#/$defs/relationName."
        )

    def test_m2o_inverse_name_refs_relation_name(self, m2o):
        ref = m2o["properties"]["inverse_name"].get("$ref", "")
        assert "common.schema.json" in ref and "relationName" in ref, (
            "manyToOne.inverse_name doit référencer common.schema.json#/$defs/relationName."
        )

    def test_m2o_foreign_key_refs_column_name(self, m2o):
        ref = m2o["properties"]["foreign_key"].get("$ref", "")
        assert "common.schema.json" in ref and "columnName" in ref, (
            "manyToOne.foreign_key doit référencer common.schema.json#/$defs/columnName."
        )

    def test_m2o_nullable_is_boolean(self, m2o):
        assert m2o["properties"]["nullable"].get("type") == "boolean", (
            "manyToOne.nullable doit être de type boolean."
        )

    def test_m2o_index_is_boolean(self, m2o):
        assert m2o["properties"]["index"].get("type") == "boolean", (
            "manyToOne.index doit être de type boolean."
        )

    def test_m2o_on_delete_refs_on_delete(self, m2o):
        ref = m2o["properties"]["on_delete"].get("$ref", "")
        assert "common.schema.json" in ref and "onDelete" in ref, (
            "manyToOne.on_delete doit référencer common.schema.json#/$defs/onDelete."
        )

    def test_m2o_only_expected_properties(self, m2o):
        props = set(m2o.get("properties", {}).keys())
        unexpected = props - _M2O_EXPECTED_PROPS
        assert not unexpected, (
            f"manyToOne contient des propriétés inattendues : {unexpected}."
        )


class TestManyToMany:
    def test_m2m_type_is_object(self, m2m):
        assert m2m.get("type") == "object", "manyToMany doit être de type object."

    def test_m2m_additional_properties_false(self, m2m):
        assert m2m.get("additionalProperties") is False, (
            "manyToMany doit avoir additionalProperties false."
        )

    @pytest.mark.parametrize("field", sorted(_M2M_REQUIRED))
    def test_m2m_required_contains(self, m2m, field):
        assert field in m2m.get("required", []), (
            f"manyToMany.required doit contenir '{field}'."
        )

    def test_m2m_required_exact(self, m2m):
        required = set(m2m.get("required", []))
        assert required == _M2M_REQUIRED, (
            f"manyToMany.required contient des champs inattendus ou manquants : "
            f"inattendus={required - _M2M_REQUIRED}, manquants={_M2M_REQUIRED - required}."
        )

    def test_m2m_type_is_const_many_to_many(self, m2m):
        assert m2m["properties"]["type"].get("const") == "many_to_many", (
            "manyToMany.type doit être const 'many_to_many'."
        )

    def test_m2m_from_refs_entity_name(self, m2m):
        ref = m2m["properties"]["from"].get("$ref", "")
        assert "common.schema.json" in ref and "entityName" in ref, (
            "manyToMany.from doit référencer common.schema.json#/$defs/entityName."
        )

    def test_m2m_to_refs_entity_name(self, m2m):
        ref = m2m["properties"]["to"].get("$ref", "")
        assert "common.schema.json" in ref and "entityName" in ref, (
            "manyToMany.to doit référencer common.schema.json#/$defs/entityName."
        )

    def test_m2m_name_refs_relation_name(self, m2m):
        ref = m2m["properties"]["name"].get("$ref", "")
        assert "common.schema.json" in ref and "relationName" in ref, (
            "manyToMany.name doit référencer common.schema.json#/$defs/relationName."
        )

    def test_m2m_inverse_name_refs_relation_name(self, m2m):
        ref = m2m["properties"]["inverse_name"].get("$ref", "")
        assert "common.schema.json" in ref and "relationName" in ref, (
            "manyToMany.inverse_name doit référencer common.schema.json#/$defs/relationName."
        )

    def test_m2m_pivot_refs_pivot_schema(self, m2m):
        ref = m2m["properties"]["pivot"].get("$ref", "")
        assert "pivot.schema.json" in ref, (
            "manyToMany.pivot doit référencer pivot.schema.json."
        )

    def test_m2m_only_expected_properties(self, m2m):
        props = set(m2m.get("properties", {}).keys())
        unexpected = props - _M2M_EXPECTED_PROPS
        assert not unexpected, (
            f"manyToMany contient des propriétés inattendues : {unexpected}."
        )

    @pytest.mark.parametrize("prop", sorted(_M2M_FORBIDDEN_DIRECT))
    def test_m2m_does_not_carry_pivot_key_directly(self, m2m, prop):
        assert prop not in m2m.get("properties", {}), (
            f"La propriété '{prop}' ne doit pas être directement sur manyToMany "
            f"— elle appartient à l'objet pivot."
        )


class TestForbiddenRelationTypes:
    @pytest.mark.parametrize("rtype", sorted(_FORBIDDEN_RELATION_TYPES))
    def test_forbidden_type_not_in_defs(self, schema, rtype):
        defs = schema.get("$defs", {})
        assert rtype not in defs, (
            f"La définition '{rtype}' ne doit pas exister dans $defs."
        )

    @pytest.mark.parametrize("prop", sorted(_FORBIDDEN_RUNTIME))
    def test_no_runtime_property(self, schema, prop):
        props = schema.get("properties", {})
        assert prop not in props, (
            f"La propriété runtime '{prop}' ne doit pas être dans relations.schema.json."
        )
