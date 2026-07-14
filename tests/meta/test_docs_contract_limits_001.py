"""Garde-fou ENTITY-CONTRACT-DOC-008-ASSUMED-LIMITS-DOCUMENTATION.

Vérifie que docs/entities/limites-contrats-json.md existe et documente
les limites assumées des contrats JSON Schema Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "limites-contrats-json.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_limites(content):
    assert "limite" in content.lower()


def test_mentions_json_schema(content):
    assert "JSON Schema" in content


def test_mentions_validation_semantique(content):
    lower = content.lower()
    assert "sémantique" in lower or "semantique" in lower


def test_mentions_vscode(content):
    assert "VS Code" in content


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_mentions_legacy(content):
    assert "legacy" in content


def test_mentions_starters(content):
    assert "starter" in content.lower()


def test_mentions_pivot_fields(content):
    assert "pivot.fields" in content


def test_mentions_crud_avance(content):
    lower = content.lower()
    assert "crud" in lower and ("avancé" in lower or "avance" in lower)


def test_mentions_min_max(content):
    assert "min" in content and "max" in content


def test_mentions_nullable(content):
    assert "nullable" in content


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/limites-contrats-json.md" in nav
