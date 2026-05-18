"""Garde-fou ENTITY-CONTRACT-DOC-007-VSCODE-JSON-SCHEMA-AUTOCOMPLETE.

Vérifie que docs/entities/vscode-json-schema.md existe et documente correctement
l'autocomplétion VS Code avec les schémas JSON Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "vscode-json-schema.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_vscode(content):
    assert "VS Code" in content


def test_mentions_dollar_schema(content):
    assert "$schema" in content


def test_mentions_json_schemas(content):
    assert "json.schemas" in content


def test_mentions_entity_schema_json(content):
    assert "entity.schema.json" in content


def test_mentions_relations_schema_json(content):
    assert "relations.schema.json" in content


def test_mentions_pivot_schema_json(content):
    assert "pivot.schema.json" in content


def test_mentions_field_schema_json(content):
    assert "field.schema.json" in content


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_mentions_draft_2020_12(content):
    assert "Draft 2020-12" in content or "2020-12" in content


def test_vscode_does_not_replace_entity_validate(content):
    lower = content.lower()
    assert "ne remplace pas" in lower or "ne remplace" in lower


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/vscode-json-schema.md" in nav
