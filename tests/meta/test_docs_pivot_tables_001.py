"""Garde-fou ENTITY-CONTRACT-DOC-004-PIVOT-TABLES-DOCUMENTATION.

Vérifie que docs/entities/pivots-many-to-many.md existe et documente
correctement les tables pivot many_to_many de Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "pivots-many-to-many.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_many_to_many(content):
    assert "many_to_many" in content


def test_mentions_table_pivot(content):
    lower = content.lower()
    assert "table pivot" in lower or "pivot" in content


def test_mentions_id_technique(content):
    lower = content.lower()
    assert "id" in content
    assert "technique" in lower or "auto_increment" in lower or "automatique" in lower


def test_mentions_unique_pair(content):
    assert "unique_pair" in content


def test_mentions_from_key(content):
    assert "from_key" in content


def test_mentions_to_key(content):
    assert "to_key" in content


def test_mentions_pivot_fields(content):
    assert "pivot.fields" in content or ("pivot" in content and "fields" in content)


def test_mentions_forge_pivot_reserved_field(content):
    assert "FORGE_PIVOT_RESERVED_FIELD" in content


def test_mentions_create_table(content):
    assert "CREATE TABLE" in content


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/pivots-many-to-many.md" in nav
