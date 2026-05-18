"""Garde-fou ENTITY-CONTRACT-DOC-005-FORGE-TYPES-MARIADB-MAPPING.

Vérifie que docs/entities/types-forge-mariadb.md existe et documente
correctement le mapping des types Forge vers MariaDB.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOC_FILE = PROJECT_ROOT / "docs" / "entities" / "types-forge-mariadb.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"

_FORGE_TYPES = [
    "string", "text", "integer", "big_integer", "float",
    "decimal", "boolean", "date", "datetime", "email", "password", "json",
]


@pytest.fixture(scope="module")
def content() -> str:
    assert DOC_FILE.exists(), f"{DOC_FILE} introuvable"
    return DOC_FILE.read_text(encoding="utf-8")


def test_file_exists():
    assert DOC_FILE.exists()


@pytest.mark.parametrize("forge_type", _FORGE_TYPES)
def test_mentions_all_forge_types(content, forge_type):
    assert forge_type in content, f"Type Forge '{forge_type}' absent de la page"


def test_mentions_mariadb(content):
    assert "MariaDB" in content


def test_mentions_varchar(content):
    assert "VARCHAR" in content


def test_mentions_decimal(content):
    assert "DECIMAL" in content


def test_mentions_longtext(content):
    assert "LONGTEXT" in content


def test_mentions_pivot_fields(content):
    assert "pivot" in content and "fields" in content


def test_mentions_required(content):
    assert "required" in content


def test_mentions_nullable(content):
    assert "nullable" in content


def test_mentions_unique(content):
    assert "unique" in content


def test_sql_type_not_canonical(content):
    """sql_type doit être signalé comme non canonique."""
    assert "sql_type" in content
    lower = content.lower()
    assert "interdit" in lower or "ne faut pas" in lower or "pas canonique" in lower or "legacy" in lower


def test_python_type_not_canonical(content):
    """python_type doit être signalé comme non canonique."""
    assert "python_type" in content


def test_present_in_mkdocs_nav(content):
    nav = MKDOCS.read_text(encoding="utf-8")
    assert "entities/types-forge-mariadb.md" in nav
