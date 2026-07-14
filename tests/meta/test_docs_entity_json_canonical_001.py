"""Garde-fou ENTITY-CONTRACT-DOC-001-CANONICAL-JSON-ROLE.

Vérifie que docs/entities/json-canonique.md existe et contient les sections
attendues décrivant le rôle du JSON canonique dans Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "json-canonique.md"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_schema_version(content):
    assert "schema_version" in content


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_mentions_build_model(content):
    assert "build:model" in content


def test_mentions_relations_json(content):
    assert "relations.json" in content


def test_mentions_id_automatique(content):
    assert "id" in content and "automatique" in content.lower()


def test_does_not_mention_sql_type_as_canonical_key(content):
    """Le JSON canonique ne contient pas de sql_type — c'est une projection dérivée."""
    lines = content.splitlines()
    for line in lines:
        stripped = line.strip()
        if stripped.startswith(("\"sql_type\"", "'sql_type'", "sql_type:")):
            pytest.fail(
                f"docs/entities/json-canonique.md ne doit pas présenter sql_type "
                f"comme clé canonique : {line!r}"
            )


def test_mentions_forge_types(content):
    """Les types Forge supportés sont documentés."""
    assert "string" in content
    assert "integer" in content
    assert "datetime" in content


def test_mentions_many_to_many(content):
    assert "many_to_many" in content


def test_mentions_many_to_one(content):
    assert "many_to_one" in content


def test_mentions_pivot_fields(content):
    assert "pivot" in content and "fields" in content
