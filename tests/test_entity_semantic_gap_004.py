"""Garde-fou ENTITY-CANONICAL-SEMANTIC-GAP-004 (ADR-086, Level 1).

Le validateur canonique `validate_semantic` récupère les trois vérifications
sémantiques que seul `validation.py` (legacy interne) assurait jusqu'ici, et
que ni le JSON Schema ni `resolve_entity_fields` ne couvrent : mot réservé SQL
sur table/entité, source de slug, cohérence de la valeur par défaut. Ces tests
opèrent sur des entités CANONIQUES (schema_version 1.0).
"""
from __future__ import annotations

from forge_mvc_entities.entity_semantic_validate import validate_semantic
from forge_mvc_entities.entity_validation_errors import (
    FORGE_ENTITY_INVALID_DEFAULT,
    FORGE_ENTITY_INVALID_SLUG_SOURCE,
    FORGE_ENTITY_RESERVED_SQL_NAME,
)


def _entity(name="Article", table="articles", fields=None, **extra):
    return {
        "schema_version": "1.0",
        "name": name,
        "table": table,
        "fields": fields if fields is not None else [{"name": "titre", "type": "string"}],
        **extra,
    }


def _codes(entity):
    return {e.code for e in validate_semantic([("art.json", entity)], None)}


# --- Mots réservés SQL sur table / entité ---

def test_table_mot_reserve_sql_rejetee():
    assert FORGE_ENTITY_RESERVED_SQL_NAME in _codes(_entity(table="order"))


def test_entite_mot_reserve_sql_rejetee():
    # 'user' est réservé ; PascalCase 'User' -> comparaison insensible à la casse.
    assert FORGE_ENTITY_RESERVED_SQL_NAME in _codes(_entity(name="User", table="comptes"))


def test_table_normale_pas_de_reserve():
    assert FORGE_ENTITY_RESERVED_SQL_NAME not in _codes(_entity(table="articles"))


# --- Source de slug ---

def test_slug_source_champ_inexistant_rejete():
    entity = _entity(fields=[
        {"name": "titre", "type": "string"},
        {"name": "slug", "type": "slug", "source": "inexistant"},
    ])
    assert FORGE_ENTITY_INVALID_SLUG_SOURCE in _codes(entity)


def test_slug_source_auto_reference_rejetee():
    entity = _entity(fields=[
        {"name": "slug", "type": "slug", "source": "slug"},
    ])
    assert FORGE_ENTITY_INVALID_SLUG_SOURCE in _codes(entity)


def test_slug_source_valide_acceptee():
    entity = _entity(fields=[
        {"name": "titre", "type": "string"},
        {"name": "slug", "type": "slug", "source": "titre"},
    ])
    assert FORGE_ENTITY_INVALID_SLUG_SOURCE not in _codes(entity)


# --- Cohérence de la valeur par défaut ---

def test_default_type_incompatible_rejete():
    entity = _entity(fields=[{"name": "vues", "type": "integer", "default": "beaucoup"}])
    assert FORGE_ENTITY_INVALID_DEFAULT in _codes(entity)


def test_default_null_sur_champ_non_nullable_rejete():
    entity = _entity(fields=[{"name": "titre", "type": "string", "required": True, "default": None}])
    assert FORGE_ENTITY_INVALID_DEFAULT in _codes(entity)


def test_default_compatible_accepte():
    entity = _entity(fields=[
        {"name": "vues", "type": "integer", "default": 0},
        {"name": "actif", "type": "boolean", "default": True},
        {"name": "titre", "type": "string", "default": "sans titre"},
    ])
    assert FORGE_ENTITY_INVALID_DEFAULT not in _codes(entity)


def test_default_null_sur_champ_nullable_accepte():
    entity = _entity(fields=[{"name": "note", "type": "text", "nullable": True, "default": None}])
    assert FORGE_ENTITY_INVALID_DEFAULT not in _codes(entity)


def test_default_date_iso_accepte():
    entity = _entity(fields=[{"name": "jour", "type": "date", "default": "2026-07-15"}])
    assert FORGE_ENTITY_INVALID_DEFAULT not in _codes(entity)


def test_default_date_non_iso_rejete():
    entity = _entity(fields=[{"name": "jour", "type": "date", "default": "15/07/2026"}])
    assert FORGE_ENTITY_INVALID_DEFAULT in _codes(entity)
