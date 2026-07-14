"""Tests meta — LEGACY-TESTS-RECLASSIFY-001 : audit de reclassification des tests legacy."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

AUDIT = Path("docs/history/audits/legacy-tests-reclassification-audit-001.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_audit_existe():
    assert AUDIT.exists()


def test_audit_mentionne_format_version():
    assert "format_version" in _audit()


def test_audit_mentionne_sql_type():
    assert "sql_type" in _audit()


def test_audit_mentionne_primary_key():
    assert "primary_key" in _audit()


def test_audit_mentionne_auto_increment():
    assert "auto_increment" in _audit()


def test_audit_mentionne_schema_version():
    assert "schema_version" in _audit()


def test_audit_mentionne_categorie_a():
    content = _audit()
    assert "Catégorie A" in content or "catégorie A" in content


def test_audit_mentionne_categorie_b():
    content = _audit()
    assert "Catégorie B" in content or "catégorie B" in content


def test_audit_mentionne_categorie_c():
    content = _audit()
    assert "Catégorie C" in content or "catégorie C" in content


def test_audit_mentionne_categorie_d():
    content = _audit()
    assert "Catégorie D" in content or "catégorie D" in content


def test_audit_mentionne_tests_a_conserver():
    content = _audit()
    assert "conserver" in content or "Conserver" in content


def test_audit_mentionne_tests_a_migrer():
    content = _audit()
    assert "migrer" in content or "Migrer" in content


def test_audit_mentionne_tests_obsoletes():
    content = _audit()
    assert "obsolète" in content or "obsolètes" in content or "supprimer" in content


def test_audit_propose_legacy_tests_migrate_001():
    assert "LEGACY-TESTS-MIGRATE-001" in _audit()


def test_audit_ne_dit_pas_tests_deja_migres():
    content = _audit()
    assert "tests migrés" not in content
    assert "tous les tests sont canoniques" not in content


def test_audit_ne_dit_pas_support_legacy_supprime():
    content = _audit()
    assert "legacy supprimé" not in content
    assert "support legacy supprimé" not in content
