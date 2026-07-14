"""Garde-fou ENTITY-CONTRACT-DOC-006-ENTITY-VALIDATE-DOCUMENTATION.

Vérifie que docs/entities/entity-validate.md existe et documente correctement
la commande forge entity:validate.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "entity-validate.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_mentions_json_flag(content):
    assert "--json" in content


def test_mentions_valid_field(content):
    assert "valid" in content


def test_mentions_errors_count(content):
    assert "errors_count" in content


def test_mentions_forge_entity_schema_invalid(content):
    assert "FORGE_ENTITY_SCHEMA_INVALID" in content


def test_mentions_forge_relation_schema_invalid(content):
    assert "FORGE_RELATION_SCHEMA_INVALID" in content


def test_mentions_forge_pivot_reserved_field(content):
    assert "FORGE_PIVOT_RESERVED_FIELD" in content


def test_mentions_schema_phase(content):
    assert "schema" in content


def test_mentions_semantic_phase(content):
    assert "semantic" in content


def test_mentions_build_model(content):
    assert "build:model" in content


def test_mentions_make_crud(content):
    assert "make:crud" in content


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/entity-validate.md" in nav
