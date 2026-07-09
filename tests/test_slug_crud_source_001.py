"""SLUG-SQL-CRUD-001 (Commit B) — slug auto-généré depuis un champ source.

Un champ `{"type": "slug", "source": "titre"}` est exclu du formulaire et de
l'`UPDATE` (stable à l'édition), conservé dans l'`INSERT`, et calculé par le
contrôleur via `core.http.slug.slugify` à la création. La contrainte `UNIQUE`
garantit l'absence de doublon (le message clair est un sous-chantier séparé).

Validation runtime (DB) : déférée au dogfood. Ici : structurel + compile.
"""
from __future__ import annotations

import compileall
import os
import tempfile

import pytest

from forge_mvc_entities.canonical_model_normalizer import (
    normalize_canonical_entity_for_model_build,
)
from forge_mvc_entities.crud.controller_builder import build_controller
from forge_mvc_entities.crud.form_builder import build_form
from forge_mvc_entities.crud.model_builder import build_model
from forge_mvc_entities.validation import validate_entity_definition


def _entity(source: str = "titre") -> dict:
    return {
        "schema_version": "1.0", "name": "Article", "table": "article",
        "fields": [
            {"name": "titre", "type": "string", "max_length": 200, "required": True},
            {"name": "slug", "type": "slug", "unique": True, "required": True, "source": source},
        ],
        "options": {"timestamps": False, "soft_delete": False},
    }


def _definition(source: str = "titre") -> dict:
    return validate_entity_definition(
        normalize_canonical_entity_for_model_build(_entity(source)), source="<test>"
    )


# ── Contrat / validation ─────────────────────────────────────────────────────

class TestContract:
    def test_source_preserved_through_normalisation(self):
        slug = next(f for f in _definition()["fields"] if f["name"] == "slug")
        assert slug["source"] == "titre"

    def test_source_unknown_field_rejected(self):
        with pytest.raises(ValueError):
            _definition(source="inexistant")

    def test_source_self_reference_rejected(self):
        with pytest.raises(ValueError):
            _definition(source="slug")


# ── Génération CRUD ──────────────────────────────────────────────────────────

class TestGeneration:
    def test_form_excludes_generated_slug(self):
        code, _ = build_form(_definition(), [])
        assert "titre = StringField" in code
        assert "slug = SlugField" not in code
        assert "SlugField" not in code  # plus importé non plus

    def test_model_insert_has_slug_update_excludes_it(self):
        model = build_model(_definition())
        insert = next(line for line in model.splitlines() if line.strip().startswith("INSERT"))
        update = next(line for line in model.splitlines() if line.strip().startswith("UPDATE"))
        assert "Slug" in insert
        assert "Slug" not in update

    def test_controller_generates_slug_from_source(self):
        ctrl = build_controller(_definition())
        assert "from core.http.slug import slugify" in ctrl
        assert 'form.cleaned_data["slug"] = slugify(form.cleaned_data["titre"])' in ctrl

    def test_generated_crud_compiles(self):
        d = _definition()
        tmp = tempfile.mkdtemp()
        for name, code in [
            ("article_form.py", build_form(d, [])[0]),
            ("article_model.py", build_model(d)),
            ("article_controller.py", build_controller(d)),
        ]:
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(code)
        assert compileall.compile_dir(tmp, quiet=1)

    def test_no_slug_no_slugify_import(self):
        # Une entité sans champ généré ne tire pas core.http.slug.
        plain = {
            "schema_version": "1.0", "name": "Note", "table": "note",
            "fields": [{"name": "texte", "type": "string", "max_length": 100}],
            "options": {"timestamps": False, "soft_delete": False},
        }
        d = validate_entity_definition(
            normalize_canonical_entity_for_model_build(plain), source="<test>"
        )
        assert "from core.http.slug import slugify" not in build_controller(d)
