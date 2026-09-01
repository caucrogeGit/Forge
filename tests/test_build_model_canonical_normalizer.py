"""Garde-fou ENTITY-CONTRACT-011B.

Vérifie que normalize_canonical_entity_for_model_build() traduit correctement
le format canonique schema_version 1.0 vers la structure interne build:model.

Couverture :
- name → entity
- table conservé
- id technique ajouté automatiquement
- id ignoré depuis fields[]
- mapping de tous les types Forge (12 types)
- nullable, required, unique
- timestamps et soft_delete
- options absent ne plante pas
- indexes ignoré sans erreur
- type inconnu → erreur claire
- string sans max_length → VARCHAR(255)
- decimal sans precision/scale → erreur claire
"""
from __future__ import annotations

import pytest

from forge_mvc_entities.canonical_model_normalizer import (
    CanonicalNormalizationError,
    column_for_field,
    normalize_canonical_entity_for_model_build,
)

pytestmark = pytest.mark.meta

_normalize = normalize_canonical_entity_for_model_build


# ── Helpers ───────────────────────────────────────────────────────────────────

def _entity(fields=None, **kwargs):
    base = {
        "schema_version": "1.0",
        "name": "Article",
        "table": "articles",
        "fields": fields or [],
    }
    base.update(kwargs)
    return base


def _field(name, type_, **kwargs):
    return {"name": name, "type": type_, **kwargs}


def _find_field(result, name):
    return next((f for f in result["fields"] if f["name"] == name), None)


# ── Racine ────────────────────────────────────────────────────────────────────

class TestRootMapping:
    def test_name_becomes_entity(self):
        result = _normalize(_entity())
        assert result["entity"] == "Article"

    def test_table_preserved(self):
        result = _normalize(_entity())
        assert result["table"] == "articles"

    def test_no_schema_version_in_output(self):
        result = _normalize(_entity())
        assert "schema_version" not in result

    def test_no_name_key_in_output(self):
        result = _normalize(_entity())
        assert "name" not in result

    def test_description_preserved_when_present(self):
        result = _normalize(_entity(description="Un article"))
        assert result["description"] == "Un article"

    def test_description_absent_when_empty(self):
        result = _normalize(_entity())
        assert "description" not in result


# ── Champ id technique ────────────────────────────────────────────────────────

class TestIdFieldGeneration:
    def test_id_added_automatically(self):
        result = _normalize(_entity())
        assert _find_field(result, "id") is not None

    def test_id_is_primary_key(self):
        result = _normalize(_entity())
        id_f = _find_field(result, "id")
        assert id_f["primary_key"] is True

    def test_id_is_auto_increment(self):
        result = _normalize(_entity())
        id_f = _find_field(result, "id")
        assert id_f["auto_increment"] is True

    def test_id_sql_type(self):
        result = _normalize(_entity())
        id_f = _find_field(result, "id")
        assert id_f["sql_type"] == "BIGINT UNSIGNED"

    def test_id_python_type(self):
        result = _normalize(_entity())
        id_f = _find_field(result, "id")
        assert id_f["python_type"] == "int"

    def test_id_not_nullable(self):
        result = _normalize(_entity())
        id_f = _find_field(result, "id")
        assert id_f["nullable"] is False

    def test_id_is_first_field(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=255)]))
        assert result["fields"][0]["name"] == "id"

    def test_id_from_fields_is_ignored(self):
        result = _normalize(_entity(fields=[_field("id", "string", max_length=100)]))
        id_fields = [f for f in result["fields"] if f["name"] == "id"]
        assert len(id_fields) == 1
        assert id_fields[0]["primary_key"] is True

    def test_id_from_fields_ignored_only_one_id(self):
        result = _normalize(_entity(fields=[_field("id", "integer")]))
        assert sum(1 for f in result["fields"] if f["name"] == "id") == 1


# ── Mapping types Forge ───────────────────────────────────────────────────────

class TestTypeMapping:
    def test_string_sql_type(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100)]))
        f = _find_field(result, "title")
        assert f["sql_type"] == "VARCHAR(100)"

    def test_string_python_type(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100)]))
        f = _find_field(result, "title")
        assert f["python_type"] == "str"

    def test_text_sql_type(self):
        result = _normalize(_entity(fields=[_field("body", "text")]))
        f = _find_field(result, "body")
        assert f["sql_type"] == "TEXT"

    def test_text_python_type(self):
        result = _normalize(_entity(fields=[_field("body", "text")]))
        f = _find_field(result, "body")
        assert f["python_type"] == "str"

    def test_integer_sql_type(self):
        result = _normalize(_entity(fields=[_field("count", "integer")]))
        f = _find_field(result, "count")
        assert f["sql_type"] == "INT"

    def test_integer_python_type(self):
        result = _normalize(_entity(fields=[_field("count", "integer")]))
        f = _find_field(result, "count")
        assert f["python_type"] == "int"

    def test_big_integer_sql_type(self):
        result = _normalize(_entity(fields=[_field("views", "big_integer")]))
        f = _find_field(result, "views")
        assert f["sql_type"] == "BIGINT"

    def test_big_integer_python_type(self):
        result = _normalize(_entity(fields=[_field("views", "big_integer")]))
        f = _find_field(result, "views")
        assert f["python_type"] == "int"

    def test_float_sql_type(self):
        result = _normalize(_entity(fields=[_field("score", "float")]))
        f = _find_field(result, "score")
        assert f["sql_type"] == "DOUBLE"

    def test_float_python_type(self):
        result = _normalize(_entity(fields=[_field("score", "float")]))
        f = _find_field(result, "score")
        assert f["python_type"] == "float"

    def test_decimal_sql_type(self):
        result = _normalize(_entity(fields=[_field("price", "decimal", precision=10, scale=2)]))
        f = _find_field(result, "price")
        assert f["sql_type"] == "DECIMAL(10,2)"

    def test_decimal_python_type(self):
        result = _normalize(_entity(fields=[_field("price", "decimal", precision=10, scale=2)]))
        f = _find_field(result, "price")
        assert f["python_type"] == "float"

    def test_boolean_sql_type(self):
        result = _normalize(_entity(fields=[_field("active", "boolean")]))
        f = _find_field(result, "active")
        assert f["sql_type"] == "BOOLEAN"

    def test_boolean_python_type(self):
        result = _normalize(_entity(fields=[_field("active", "boolean")]))
        f = _find_field(result, "active")
        assert f["python_type"] == "bool"

    def test_date_sql_type(self):
        result = _normalize(_entity(fields=[_field("birth_date", "date")]))
        f = _find_field(result, "birth_date")
        assert f["sql_type"] == "DATE"

    def test_date_python_type(self):
        result = _normalize(_entity(fields=[_field("birth_date", "date")]))
        f = _find_field(result, "birth_date")
        assert f["python_type"] == "date"

    def test_datetime_sql_type(self):
        result = _normalize(_entity(fields=[_field("published_at", "datetime")]))
        f = _find_field(result, "published_at")
        assert f["sql_type"] == "DATETIME"

    def test_datetime_python_type(self):
        result = _normalize(_entity(fields=[_field("published_at", "datetime")]))
        f = _find_field(result, "published_at")
        assert f["python_type"] == "datetime"

    def test_email_sql_type(self):
        result = _normalize(_entity(fields=[_field("email", "email")]))
        f = _find_field(result, "email")
        assert f["sql_type"] == "VARCHAR(255)"

    def test_email_python_type(self):
        result = _normalize(_entity(fields=[_field("email", "email")]))
        f = _find_field(result, "email")
        assert f["python_type"] == "str"

    def test_password_sql_type(self):
        result = _normalize(_entity(fields=[_field("password", "password")]))
        f = _find_field(result, "password")
        assert f["sql_type"] == "VARCHAR(255)"

    def test_password_python_type(self):
        result = _normalize(_entity(fields=[_field("password", "password")]))
        f = _find_field(result, "password")
        assert f["python_type"] == "str"

    def test_json_sql_type(self):
        result = _normalize(_entity(fields=[_field("meta", "json")]))
        f = _find_field(result, "meta")
        assert f["sql_type"] == "LONGTEXT"

    def test_json_python_type(self):
        result = _normalize(_entity(fields=[_field("meta", "json")]))
        f = _find_field(result, "meta")
        assert f["python_type"] == "str"


# ── Contraintes nullable / required / unique ──────────────────────────────────

class TestConstraints:
    def test_required_true_produces_not_null(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100, required=True)]))
        f = _find_field(result, "title")
        assert f["nullable"] is False

    def test_nullable_false_produces_not_null(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100, nullable=False)]))
        f = _find_field(result, "title")
        assert f["nullable"] is False

    def test_nullable_true_does_not_produce_not_null(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100, nullable=True)]))
        f = _find_field(result, "title")
        assert f["nullable"] is True

    def test_default_nullable_is_true(self):
        # ADR-013 : nullable par défaut (True = NULL)
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100)]))
        f = _find_field(result, "title")
        assert f["nullable"] is True

    def test_required_false_without_nullable_is_null(self):
        # ADR-013 : required: false seul → NULL
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100, required=False)]))
        f = _find_field(result, "title")
        assert f["nullable"] is True

    def test_required_true_overrides_nullable_true(self):
        # ADR-013 : required: true gagne même si nullable: true
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100, required=True, nullable=True)]))
        f = _find_field(result, "title")
        assert f["nullable"] is False

    def test_unique_true_in_output(self):
        result = _normalize(_entity(fields=[_field("slug", "string", max_length=100, unique=True)]))
        f = _find_field(result, "slug")
        assert f["unique"] is True

    def test_unique_false_by_default(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100)]))
        f = _find_field(result, "title")
        assert f["unique"] is False

    def test_min_mapped_to_min_value_for_integer(self):
        result = _normalize(_entity(fields=[_field("age", "integer", min=0)]))
        f = _find_field(result, "age")
        assert f["constraints"]["min_value"] == 0

    def test_max_mapped_to_max_value_for_integer(self):
        result = _normalize(_entity(fields=[_field("age", "integer", max=120)]))
        f = _find_field(result, "age")
        assert f["constraints"]["max_value"] == 120

    def test_min_max_absent_for_non_numeric_type(self):
        result = _normalize(_entity(fields=[_field("title", "string", max_length=100, min=0)]))
        f = _find_field(result, "title")
        assert "min_value" not in f["constraints"]


# ── Champs système ────────────────────────────────────────────────────────────

class TestSystemFields:
    def test_timestamps_adds_created_at(self):
        result = _normalize(_entity(options={"timestamps": True}))
        assert _find_field(result, "created_at") is not None

    def test_timestamps_adds_updated_at(self):
        result = _normalize(_entity(options={"timestamps": True}))
        assert _find_field(result, "updated_at") is not None

    def test_timestamps_created_at_sql_type(self):
        result = _normalize(_entity(options={"timestamps": True}))
        f = _find_field(result, "created_at")
        assert f["sql_type"] == "DATETIME"

    def test_timestamps_updated_at_not_nullable(self):
        result = _normalize(_entity(options={"timestamps": True}))
        f = _find_field(result, "updated_at")
        assert f["nullable"] is False

    def test_soft_delete_adds_deleted_at(self):
        result = _normalize(_entity(options={"soft_delete": True}))
        assert _find_field(result, "deleted_at") is not None

    def test_soft_delete_deleted_at_nullable(self):
        result = _normalize(_entity(options={"soft_delete": True}))
        f = _find_field(result, "deleted_at")
        assert f["nullable"] is True

    def test_soft_delete_deleted_at_sql_type(self):
        result = _normalize(_entity(options={"soft_delete": True}))
        f = _find_field(result, "deleted_at")
        assert f["sql_type"] == "DATETIME"

    def test_options_absent_does_not_raise(self):
        result = _normalize(_entity())
        assert result is not None

    def test_options_none_does_not_raise(self):
        entity = _entity()
        entity["options"] = None
        result = _normalize(entity)
        assert result is not None

    def test_timestamps_false_no_created_at(self):
        result = _normalize(_entity(options={"timestamps": False}))
        assert _find_field(result, "created_at") is None

    def test_soft_delete_false_no_deleted_at(self):
        result = _normalize(_entity(options={"soft_delete": False}))
        assert _find_field(result, "deleted_at") is None


# ── Mapping champ vers colonne (ADR-069 / ADR-077) ────────────────────────────

class TestColumnForField:
    """`column_for_field` : source unique du mapping champ vers colonne SQL."""

    def test_ordinary_field_is_pascal_case(self):
        assert column_for_field(_field("date_naissance", "date")) == "DateNaissance"

    def test_single_word_field_is_capitalised(self):
        assert column_for_field(_field("nom", "string")) == "Nom"

    def test_foreign_key_keeps_snake_case(self):
        assert column_for_field(_field("annee_scolaire_id", "foreign_key")) == "annee_scolaire_id"

    def test_matches_normalizer_column(self):
        # La colonne exposée par la fonction publique coïncide avec celle que le
        # normaliseur écrit dans le modèle (une seule source de vérité).
        result = _normalize(_entity(fields=[
            _field("user_id", "foreign_key"),
            _field("date_naissance", "date"),
        ]))
        assert _find_field(result, "user_id")["column"] == column_for_field(
            _field("user_id", "foreign_key")
        )
        assert _find_field(result, "date_naissance")["column"] == column_for_field(
            _field("date_naissance", "date")
        )


# ── Indexes ignorés ───────────────────────────────────────────────────────────

class TestIndexesPortes:
    """Les index étaient écartés ici, et n'atteignaient donc jamais le SQL.

    Ce groupe figeait ce comportement, `test_indexes_not_in_output` vérifiant
    leur absence. C'était le défaut, pas la règle : une contrainte d'unicité
    composite passait la validation sans jamais contraindre quoi que ce soit
    (`ENTITIES-UNIQUE-COMPOSITE-001`).
    """

    def test_indexes_key_does_not_raise(self):
        entity = _entity(fields=[_field("slug", "string", max_length=100)])
        entity["indexes"] = [{"name": "idx_slug", "fields": ["slug"]}]
        result = _normalize(entity)
        assert result is not None

    def test_indexes_in_output(self):
        entity = _entity(fields=[_field("slug", "string", max_length=100)])
        entity["indexes"] = [{"name": "idx_slug", "fields": ["slug"]}]
        result = _normalize(entity)
        assert result["indexes"] == [
            {"name": "idx_slug", "columns": ["Slug"], "unique": False}
        ]

    def test_unique_composite_est_porte(self):
        entity = _entity(fields=[
            _field("slug", "string", max_length=100),
            _field("code", "string", max_length=20),
        ])
        entity["indexes"] = [
            {"name": "uq_slug_code", "fields": ["slug", "code"], "unique": True}
        ]
        result = _normalize(entity)
        assert result["indexes"][0]["unique"] is True
        assert result["indexes"][0]["columns"] == ["Slug", "Code"]

    def test_sans_index_la_cle_reste_absente(self):
        result = _normalize(_entity(fields=[_field("slug", "string", max_length=100)]))
        assert "indexes" not in result


# ── Cas d'erreur ──────────────────────────────────────────────────────────────

class TestErrorCases:
    def test_unknown_type_raises_error(self):
        with pytest.raises(CanonicalNormalizationError):
            _normalize(_entity(fields=[_field("thing", "unknown_type")]))

    def test_unknown_type_error_message_contains_type(self):
        with pytest.raises(CanonicalNormalizationError, match="unknown_type"):
            _normalize(_entity(fields=[_field("thing", "unknown_type")]))

    def test_decimal_without_precision_raises_error(self):
        with pytest.raises(CanonicalNormalizationError):
            _normalize(_entity(fields=[_field("price", "decimal", scale=2)]))

    def test_decimal_without_scale_raises_error(self):
        with pytest.raises(CanonicalNormalizationError):
            _normalize(_entity(fields=[_field("price", "decimal", precision=10)]))

    def test_decimal_without_both_raises_error(self):
        with pytest.raises(CanonicalNormalizationError):
            _normalize(_entity(fields=[_field("price", "decimal")]))

    def test_string_without_max_length_uses_255(self):
        result = _normalize(_entity(fields=[_field("title", "string")]))
        f = _find_field(result, "title")
        assert f["sql_type"] == "VARCHAR(255)"

    def test_string_with_invalid_max_length_raises(self):
        with pytest.raises(CanonicalNormalizationError):
            _normalize(_entity(fields=[_field("title", "string", max_length=0)]))

    def test_string_with_negative_max_length_raises(self):
        with pytest.raises(CanonicalNormalizationError):
            _normalize(_entity(fields=[_field("title", "string", max_length=-1)]))


# ── Compatibilité validateur legacy ──────────────────────────────────────────

class TestLegacyCompatibility:
    """Vérifie que la sortie passe normalize_entity_definition() sans erreur."""

    def test_simple_entity_passes_legacy_validator(self):
        from forge_mvc_entities.validation import normalize_entity_definition
        result = _normalize(_entity(fields=[_field("title", "string", max_length=255)]))
        normalized = normalize_entity_definition(result)
        assert normalized["entity"] == "Article"

    def test_all_types_pass_legacy_validator(self):
        from forge_mvc_entities.validation import normalize_entity_definition
        fields = [
            _field("title", "string", max_length=100),
            _field("body", "text"),
            _field("count", "integer"),
            _field("views", "big_integer"),
            _field("score", "float"),
            _field("price", "decimal", precision=10, scale=2),
            _field("active", "boolean"),
            _field("birth_date", "date"),
            _field("published_at", "datetime"),
            _field("email", "email"),
            _field("password", "password"),
            _field("meta", "json"),
        ]
        result = _normalize(_entity(fields=fields))
        normalized = normalize_entity_definition(result)
        assert normalized["entity"] == "Article"

    def test_timestamps_pass_legacy_validator(self):
        from forge_mvc_entities.validation import normalize_entity_definition
        result = _normalize(_entity(
            fields=[_field("title", "string", max_length=100)],
            options={"timestamps": True},
        ))
        normalized = normalize_entity_definition(result)
        field_names = [f["name"] for f in normalized["fields"]]
        assert "created_at" in field_names
        assert "updated_at" in field_names
