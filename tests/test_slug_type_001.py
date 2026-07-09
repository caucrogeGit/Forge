"""SLUG-SQL-CRUD-001 (Commit A) — `slug` comme type canonique d'entité.

Un champ `{"type": "slug"}` se normalise en colonne `VARCHAR(180)` + widget
`SlugField` (ADR-017 D3). Étape A : le type slug existe et génère un formulaire
correct (saisie manuelle validée). L'auto-génération depuis un champ source est
l'étape B (`source`).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from forge_mvc_entities.canonical_model_normalizer import (
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.crud.form_builder import build_form
from forge_mvc_entities.validation import validate_entity_definition

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CANONICAL = {
    "schema_version": "1.0",
    "name": "Article",
    "table": "article",
    "fields": [
        {"name": "titre", "type": "string", "max_length": 200, "required": True},
        {"name": "slug", "type": "slug", "unique": True, "required": True},
    ],
    "options": {"timestamps": False, "soft_delete": False},
}


def _normalized() -> dict:
    return normalize_canonical_entity_for_model_build(dict(CANONICAL))


class TestNormalizer:
    def test_slug_field_canonical_mapping(self):
        slug = next(f for f in _normalized()["fields"] if f["name"] == "slug")
        assert slug["sql_type"] == "VARCHAR(180)"
        assert slug["python_type"] == "str"
        assert slug["form"] == {"field": "slug"}
        assert slug["constraints"]["max_length"] == 180
        assert slug["unique"] is True

    def test_normalized_validates(self):
        # Ne lève pas : le champ slug normalisé respecte le contrat legacy.
        validate_entity_definition(_normalized(), source="<test>")


class TestCrudFormGeneration:
    def test_slug_generates_slugfield(self):
        definition = validate_entity_definition(_normalized(), source="<test>")
        code, _warnings = build_form(definition, [])
        assert "SlugField(" in code
        assert "max_length=180" in code


class TestSchemaEnum:
    @pytest.mark.parametrize("rel", [
        "cli/schemas/field.schema.json",
    ])
    def test_slug_in_type_enum(self, rel):
        schema = json.loads((PROJECT_ROOT / rel).read_text(encoding="utf-8"))
        assert "slug" in schema["properties"]["type"]["enum"]
