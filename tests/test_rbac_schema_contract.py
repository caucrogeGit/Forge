"""Tests — RBAC-CONTRACT-002 : contrat JSON Schema du fichier rbac.json.

Vérifie que rbac.schema.json est conforme, que les deux copies sont identiques,
et que entity.schema.json ne contient pas de propriété rbac.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent

SCHEMA_SOURCE = PROJECT_ROOT / "schemas" / "rbac.schema.json"
SCHEMA_PACKAGED = PROJECT_ROOT / "cli" / "schemas" / "rbac.schema.json"
ENTITY_SCHEMA = PROJECT_ROOT / "schemas" / "entity.schema.json"

_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _make_validator(schema: dict):
    """Construit un validateur Draft 2020-12 avec registre local (identique à entity_validate.py)."""
    from referencing import Registry, Resource
    from referencing.jsonschema import DRAFT202012
    from jsonschema import Draft202012Validator

    schemas_dir = SCHEMA_SOURCE.parent
    resources = []
    for f in schemas_dir.glob("*.json"):
        try:
            s = json.loads(f.read_text(encoding="utf-8"))
            if "$id" in s:
                resources.append(
                    (s["$id"], Resource.from_contents(s, default_specification=DRAFT202012))
                )
        except Exception:
            pass
    registry = Registry().with_resources(resources)
    return Draft202012Validator(schema, registry=registry)


def _validate(instance: dict, schema: dict) -> None:
    _make_validator(schema).validate(instance)


# ── Existence ──────────────────────────────────────────────────────────────────


def test_schema_source_existe():
    assert SCHEMA_SOURCE.exists()


def test_schema_packaged_existe():
    assert SCHEMA_PACKAGED.exists()


# ── Les deux copies sont identiques ──────────────────────────────────────────


def test_schemas_identiques():
    assert SCHEMA_SOURCE.read_text(encoding="utf-8") == SCHEMA_PACKAGED.read_text(encoding="utf-8")


# ── Méta-données du schéma ────────────────────────────────────────────────────


def test_schema_declare_draft_2020_12():
    schema = _load(SCHEMA_SOURCE)
    assert schema.get("$schema") == _DRAFT_2020_12


def test_schema_a_un_titre():
    schema = _load(SCHEMA_SOURCE)
    assert "title" in schema
    assert "RBAC" in schema["title"] or "rbac" in schema["title"].lower()


def test_schema_additional_properties_false():
    schema = _load(SCHEMA_SOURCE)
    assert schema.get("additionalProperties") is False


# ── schema_version obligatoire ────────────────────────────────────────────────


def test_schema_version_est_obligatoire():
    schema = _load(SCHEMA_SOURCE)
    assert "schema_version" in schema.get("required", [])


def test_schema_version_refuse_valeur_incorrecte():
    from jsonschema import ValidationError

    schema = _load(SCHEMA_SOURCE)
    with pytest.raises(ValidationError):
        _validate({"schema_version": "2.0"}, schema)


def test_schema_version_accepte_1_0():
    schema = _load(SCHEMA_SOURCE)
    _validate({"schema_version": "1.0"}, schema)


# ── Contrat minimal valide ────────────────────────────────────────────────────


def test_contrat_minimal_valide():
    schema = _load(SCHEMA_SOURCE)
    _validate({"schema_version": "1.0"}, schema)


def test_contrat_avec_roles_valide():
    schema = _load(SCHEMA_SOURCE)
    instance = {
        "schema_version": "1.0",
        "roles": {
            "admin": ["article.list", "article.create"],
            "reader": ["article.list"],
        },
    }
    _validate(instance, schema)


def test_contrat_avec_entities_valide():
    schema = _load(SCHEMA_SOURCE)
    instance = {
        "schema_version": "1.0",
        "entities": {
            "Article": {
                "permissions": {
                    "list": "article.list",
                    "create": "article.create",
                }
            }
        },
    }
    _validate(instance, schema)


def test_contrat_complet_valide():
    schema = _load(SCHEMA_SOURCE)
    instance = {
        "schema_version": "1.0",
        "entities": {
            "Article": {
                "permissions": {
                    "list":   "article.list",
                    "show":   "article.show",
                    "create": "article.create",
                    "update": "article.update",
                    "delete": "article.delete",
                }
            }
        },
        "roles": {
            "admin": [
                "article.list",
                "article.show",
                "article.create",
                "article.update",
                "article.delete",
            ],
            "editor": ["article.list", "article.show", "article.create"],
            "reader": ["article.list", "article.show"],
        },
    }
    _validate(instance, schema)


# ── Refus des formats incorrects ──────────────────────────────────────────────


def test_propriete_racine_inconnue_refusee():
    from jsonschema import ValidationError

    schema = _load(SCHEMA_SOURCE)
    with pytest.raises(ValidationError):
        _validate({"schema_version": "1.0", "cle_inconnue": "valeur"}, schema)


def test_role_non_tableau_refuse():
    from jsonschema import ValidationError

    schema = _load(SCHEMA_SOURCE)
    with pytest.raises(ValidationError):
        _validate({"schema_version": "1.0", "roles": {"admin": "article.list"}}, schema)


def test_permission_non_string_refusee():
    from jsonschema import ValidationError

    schema = _load(SCHEMA_SOURCE)
    with pytest.raises(ValidationError):
        _validate({"schema_version": "1.0", "roles": {"admin": [42]}}, schema)


# ── entity.schema.json inchangé ───────────────────────────────────────────────


def test_entity_schema_ne_contient_pas_rbac():
    schema = _load(ENTITY_SCHEMA)
    assert "rbac" not in schema.get("properties", {})


def test_entity_schema_additional_properties_false():
    schema = _load(ENTITY_SCHEMA)
    assert schema.get("additionalProperties") is False
