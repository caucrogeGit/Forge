"""Tests meta — LEGACY-MIGRATION-001 : guide de migration legacy vers canonique."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

GUIDE = Path("docs/entities/migration-legacy-vers-canonique.md")
MKDOCS = Path("mkdocs.yml")


def _guide() -> str:
    return GUIDE.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_guide_existe():
    assert GUIDE.exists()


# ── Contenu obligatoire — clés legacy ─────────────────────────────────────────


def test_guide_mentionne_format_version():
    assert "format_version" in _guide()


def test_guide_mentionne_schema_version():
    assert "schema_version" in _guide()


def test_guide_mentionne_sql_type():
    assert "sql_type" in _guide()


def test_guide_mentionne_python_type():
    assert "python_type" in _guide()


def test_guide_mentionne_primary_key():
    assert "primary_key" in _guide()


def test_guide_mentionne_auto_increment():
    assert "auto_increment" in _guide()


def test_guide_mentionne_from_entity():
    assert "from_entity" in _guide()


def test_guide_mentionne_foreign_key_name():
    assert "foreign_key_name" in _guide()


# ── Contenu obligatoire — relations ───────────────────────────────────────────


def test_guide_mentionne_many_to_one():
    assert "many_to_one" in _guide()


def test_guide_mentionne_many_to_many():
    assert "many_to_many" in _guide()


def test_guide_mentionne_pivot():
    assert "pivot" in _guide()


# ── Contenu obligatoire — commandes ───────────────────────────────────────────


def test_guide_mentionne_entity_validate():
    assert "entity:validate" in _guide()


def test_guide_mentionne_build_model():
    assert "build:model" in _guide()


# ── Contenu obligatoire — politique ───────────────────────────────────────────


def test_guide_mentionne_legacy_deprecie():
    content = _guide()
    assert "déprécié" in content or "Déprécié" in content


def test_guide_mentionne_adr_012():
    assert "ADR-012" in _guide()


# ── MkDocs ────────────────────────────────────────────────────────────────────


def test_guide_present_dans_mkdocs():
    content = MKDOCS.read_text(encoding="utf-8")
    assert "migration-legacy-vers-canonique.md" in content
