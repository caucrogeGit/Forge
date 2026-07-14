"""Garde-fou ENTITY-CONTRACT-DOC-003-RELATIONS-SCHEMA-DOCUMENTATION.

Vérifie que docs/entities/relations-schema.md existe et documente correctement
le contrat relations.schema.json de Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "relations-schema.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_relations_schema_json(content):
    assert "relations.schema.json" in content


def test_mentions_schema_version(content):
    assert "schema_version" in content


def test_mentions_relations_json(content):
    assert "relations.json" in content


def test_mentions_many_to_one(content):
    assert "many_to_one" in content


def test_mentions_many_to_many(content):
    assert "many_to_many" in content


def test_mentions_pivot(content):
    assert "pivot" in content


def test_mentions_id_technique(content):
    """Le pivot possède toujours un id technique AUTO_INCREMENT."""
    lower = content.lower()
    assert "id" in content
    assert "technique" in lower or "auto_increment" in lower or "automatique" in lower


def test_mentions_unique_pair(content):
    assert "unique_pair" in content


def test_mentions_on_delete(content):
    assert "on_delete" in content


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_from_entity_not_canonical(content):
    """from_entity est une clé legacy — la page doit le signaler."""
    assert "from_entity" in content


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/relations-schema.md" in nav
