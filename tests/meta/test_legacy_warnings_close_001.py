"""Tests meta — LEGACY-WARNINGS-CLOSE-001 : clôture du bloc warnings legacy."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT = Path("docs/history/audits/legacy-warnings-audit-001.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_audit_existe():
    assert AUDIT.exists()


def test_audit_mentionne_cloture():
    content = _audit()
    assert "Clôture" in content or "clôture" in content or "terminé" in content


def test_audit_mentionne_legacy_warnings_001():
    assert "LEGACY-WARNINGS-001" in _audit()


def test_audit_mentionne_legacy_warnings_002():
    assert "LEGACY-WARNINGS-002" in _audit()


def test_audit_mentionne_legacy_warnings_003():
    assert "LEGACY-WARNINGS-003" in _audit()


def test_audit_mentionne_legacy_warnings_004():
    assert "LEGACY-WARNINGS-004" in _audit()


def test_audit_mentionne_build_model():
    assert "build:model" in _audit()


def test_audit_mentionne_make_crud():
    assert "make:crud" in _audit()


def test_audit_mentionne_make_relation_sans_warning():
    content = _audit()
    assert "make:relation" in content
    assert "Pas de warning" in content or "sans warning" in content or "volontairement" in content


def test_audit_mentionne_entity_validate_canonique():
    content = _audit()
    assert "entity:validate" in content
    assert "canonique" in content or "schema_version" in content


def test_audit_mentionne_non_bloquant():
    content = _audit()
    assert "non bloquant" in content or "non bloquants" in content


def test_audit_ne_dit_pas_legacy_supprime():
    content = _audit()
    assert "legacy supprimé" not in content
    assert "support legacy supprimé" not in content
    assert "suppression du legacy" not in content.lower()


def test_audit_ne_dit_pas_pypi_publie():
    content = _audit()
    assert "PyPI publié" not in content
    assert "forge-mvc publié" not in content
