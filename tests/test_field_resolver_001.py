"""Garde-fou ENTITY-RESOLVER-001 (ADR-086).

Le service `field_resolver` est la source unique du mapping type canonique vers
(sql_type, python_type, column). Ces tests caractérisent son API publique et
vérifient que le pont `canonical_model_normalizer` délègue bien au service
(iso-comportement : mêmes valeurs qu'avant l'extraction).

Le mapping sql_type est dialectal ; la suite force DB_BACKEND=mariadb (conftest),
donc les valeurs SQL attendues sont celles du dialecte MariaDB.
"""
from __future__ import annotations

import pytest

from forge_mvc_entities import field_resolver
from forge_mvc_entities.canonical_model_normalizer import (
    column_for_field,
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.field_resolver import (
    CanonicalNormalizationError,
    column_of,
    python_type_of,
    resolve_sql_and_python_type,
    sql_type_of,
)


# --- column_of : colonne d'un champ canonique ---

def test_column_of_champ_simple_pascalcase():
    assert column_of({"name": "nom_complet", "type": "string"}) == "NomComplet"


def test_column_of_foreign_key_garde_snake_case():
    assert column_of({"name": "annee_scolaire_id", "type": "foreign_key"}) == "annee_scolaire_id"


def test_column_for_field_delegue_au_service():
    # Le pont expose toujours column_for_field (API publique, fixtures ADR-077),
    # mais délègue désormais à field_resolver.column_of.
    field = {"name": "user_id", "type": "foreign_key"}
    assert column_for_field(field) == column_of(field)


# --- resolve_sql_and_python_type : mapping type -> (sql_type, python_type) ---

@pytest.mark.parametrize(
    ("forge_type", "expected_python"),
    [
        ("text", "str"),
        ("integer", "int"),
        ("big_integer", "int"),
        ("float", "float"),
        ("boolean", "bool"),
        ("date", "date"),
        ("datetime", "datetime"),
        ("email", "str"),
        ("password", "str"),
        ("slug", "str"),
        ("json", "str"),
    ],
)
def test_python_type_des_types_simples(forge_type, expected_python):
    assert python_type_of({"name": "champ", "type": forge_type}) == expected_python


def test_string_utilise_max_length():
    sql, python = resolve_sql_and_python_type({"name": "titre", "type": "string", "max_length": 120})
    assert "120" in sql
    assert python == "str"


def test_string_max_length_invalide_leve():
    with pytest.raises(CanonicalNormalizationError):
        resolve_sql_and_python_type({"name": "titre", "type": "string", "max_length": 0})


def test_decimal_requiert_precision_et_scale():
    with pytest.raises(CanonicalNormalizationError):
        resolve_sql_and_python_type({"name": "prix", "type": "decimal"})


def test_decimal_valide():
    sql, python = resolve_sql_and_python_type(
        {"name": "prix", "type": "decimal", "precision": 10, "scale": 2}
    )
    assert "10" in sql and "2" in sql
    assert python == "float"


def test_foreign_key_prend_le_type_identite():
    sql, python = resolve_sql_and_python_type({"name": "user_id", "type": "foreign_key"})
    assert sql == field_resolver.dialect().identity_type()
    assert python == "int"


def test_type_inconnu_leve():
    with pytest.raises(CanonicalNormalizationError):
        resolve_sql_and_python_type({"name": "x", "type": "inexistant"})


def test_sql_type_of_est_le_premier_element():
    field = {"name": "titre", "type": "string", "max_length": 50}
    assert sql_type_of(field) == resolve_sql_and_python_type(field)[0]


# --- Non-régression : le pont produit toujours le même dict via le service ---

def test_normalize_canonical_delegue_types_au_service():
    entity = {
        "name": "Article",
        "table": "articles",
        "fields": [
            {"name": "title", "type": "string", "max_length": 255, "required": True},
            {"name": "views", "type": "integer"},
        ],
    }
    result = normalize_canonical_entity_for_model_build(entity)
    by_name = {f["name"]: f for f in result["fields"]}

    # Le champ id synthétique reste inchangé.
    assert by_name["id"]["primary_key"] is True
    assert by_name["id"]["sql_type"] == field_resolver.dialect().identity_type()

    # Les types des champs métier viennent du service.
    assert by_name["title"]["sql_type"] == sql_type_of({"name": "title", "type": "string", "max_length": 255})
    assert by_name["title"]["python_type"] == "str"
    assert by_name["views"]["python_type"] == "int"
