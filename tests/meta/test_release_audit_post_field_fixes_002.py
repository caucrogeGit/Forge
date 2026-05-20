"""
Garde-fous documentaires pour RELEASE-AUDIT-002.
Vérifie la présence et le contenu du rapport d'audit post-corrections terrain.
"""

import pytest
from pathlib import Path

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "docs/history/audits/release-audit-post-field-fixes-002.md"


# --- existence ---

def test_audit_exists():
    assert AUDIT.exists(), f"Rapport introuvable : {AUDIT}"


def test_audit_not_empty():
    assert AUDIT.stat().st_size > 500


# --- références obligatoires ---

def test_audit_mentions_release_audit_002():
    assert "RELEASE-AUDIT-002" in AUDIT.read_text()


def test_audit_mentions_field_test_app():
    assert "FIELD-TEST-APP-001" in AUDIT.read_text()


def test_audit_mentions_field_fix_001():
    assert "FIELD-FIX-001" in AUDIT.read_text()


def test_audit_mentions_field_audit_m2m():
    assert "FIELD-AUDIT-M2M-GUARD-001" in AUDIT.read_text()


def test_audit_mentions_field_fix_m2m():
    assert "FIELD-FIX-M2M-GUARD-001" in AUDIT.read_text()


# --- frictions ---

def test_audit_mentions_f001():
    assert "F-001" in AUDIT.read_text()


def test_audit_mentions_f002():
    assert "F-002" in AUDIT.read_text()


def test_audit_mentions_f003():
    assert "F-003" in AUDIT.read_text()


# --- contenu technique ---

def test_audit_mentions_name_key():
    assert '"name"' in AUDIT.read_text()


def test_audit_mentions_entity_path_structure():
    content = AUDIT.read_text()
    assert "mvc/entities/" in content
    assert "article.json" in content or "<nom>" in content or "article/" in content


def test_audit_mentions_make_crud_article():
    assert "make:crud Article" in AUDIT.read_text()


def test_audit_mentions_make_crud_tag():
    assert "make:crud Tag" in AUDIT.read_text()


def test_audit_mentions_make_pivot_crud():
    assert "make:pivot-crud" in AUDIT.read_text()


# --- validations documentées ---

def test_audit_mentions_pytest_complet():
    content = AUDIT.read_text()
    assert "pytest" in content
    assert "passed" in content


def test_audit_mentions_mkdocs():
    assert "mkdocs" in AUDIT.read_text()


def test_audit_confirms_no_pypi():
    content = AUDIT.read_text()
    assert "PyPI" in content
    assert "NON" in content


def test_audit_confirms_no_tag():
    content = AUDIT.read_text()
    assert "Tag modifié" in content or "tag" in content.lower()
    assert "NON" in content


# --- verdict ---

def test_audit_has_verdict_ok():
    content = AUDIT.read_text()
    assert "AUDIT OK" in content


def test_audit_proposes_release_beta_next_001():
    assert "RELEASE-BETA-NEXT-001" in AUDIT.read_text()
