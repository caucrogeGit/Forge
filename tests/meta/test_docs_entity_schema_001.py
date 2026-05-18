"""Garde-fou ENTITY-CONTRACT-DOC-002-ENTITY-SCHEMA-DOCUMENTATION.

Vérifie que docs/entities/entity-schema.md existe et documente correctement
le contrat entity.schema.json de Forge.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "entity-schema.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


def test_mentions_entity_schema_json(content):
    assert "entity.schema.json" in content


def test_mentions_schema_version(content):
    assert "schema_version" in content


def test_mentions_fields(content):
    assert "fields" in content


def test_mentions_options(content):
    assert "options" in content


def test_mentions_indexes(content):
    assert "indexes" in content


def test_mentions_id_automatique(content):
    """Le champ id est géré automatiquement — ne pas le déclarer."""
    assert "id" in content
    assert "automatique" in content.lower() or "Forge l'ajoute" in content or "gérée par Forge" in content


def test_mentions_entity_validate(content):
    assert "entity:validate" in content


def test_sql_type_not_canonical(content):
    """sql_type doit être décrit comme non canonique."""
    assert "sql_type" in content
    lower = content.lower()
    assert "interdit" in lower or "n'est plus" in lower or "pas canonique" in lower or "projection" in lower


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/entity-schema.md" in nav


def test_mentions_timestamps(content):
    assert "timestamps" in content


def test_mentions_soft_delete(content):
    assert "soft_delete" in content


def test_mentions_additionalproperties(content):
    """La page doit signaler que les clés inconnues sont interdites."""
    lower = content.lower()
    assert "interdit" in lower or "clé" in lower or "inconnue" in lower
