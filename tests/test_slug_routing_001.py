"""SLUG-ROUTING-001 (ADR-017) — lookup get_<snake>_by_<slug> dans le modèle.

Pour le routing public par slug (`/articles/{slug}`), le modèle généré expose
un `get_<snake>_by_<slug>(value)` — la route elle-même reste écrite
explicitement par l'utilisateur (philosophie Forge). Généré seulement quand
l'entité a un champ de type slug.
"""
from __future__ import annotations

import compileall
import os
import tempfile

from cli.entities.canonical_model_normalizer import (
    normalize_canonical_entity_for_model_build,
)
from cli.entities.crud.model_builder import build_model
from cli.entities.validation import validate_entity_definition


def _definition(fields: list[dict], name: str = "Article", table: str = "article") -> dict:
    entity = {
        "schema_version": "1.0", "name": name, "table": table,
        "fields": fields,
        "options": {"timestamps": False, "soft_delete": False},
    }
    return validate_entity_definition(
        normalize_canonical_entity_for_model_build(entity), source="<test>"
    )


_SLUG_ENTITY = [
    {"name": "titre", "type": "string", "max_length": 200, "required": True},
    {"name": "slug", "type": "slug", "unique": True, "required": True, "source": "titre"},
]


class TestSlugLookup:
    def test_model_has_get_by_slug(self):
        model = build_model(_definition(_SLUG_ENTITY))
        assert "def get_article_by_slug(slug):" in model
        assert 'WHERE Slug = ?' in model

    def test_model_compiles(self):
        model = build_model(_definition(_SLUG_ENTITY))
        tmp = tempfile.mkdtemp()
        with open(os.path.join(tmp, "article_model.py"), "w", encoding="utf-8") as fh:
            fh.write(model)
        assert compileall.compile_dir(tmp, quiet=1)

    def test_no_slug_no_lookup(self):
        model = build_model(_definition([{"name": "texte", "type": "string", "max_length": 50}], "Note", "note"))
        assert "by_slug" not in model
