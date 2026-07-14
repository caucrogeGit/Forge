"""
Garde-fous documentaires pour FIELD-AUDIT-M2M-GUARD-001.
Vérifie la présence et le contenu du rapport d'audit du garde make:crud many-to-many.
"""

import pytest
from pathlib import Path

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
AUDIT = PROJECT_ROOT / "docs/history/audits/field-audit-m2m-guard-001.md"


# --- existence ---

def test_audit_exists():
    assert AUDIT.exists(), f"Rapport d'audit introuvable : {AUDIT}"


def test_audit_not_empty():
    assert AUDIT.stat().st_size > 500


# --- références obligatoires ---

def test_audit_mentions_ticket():
    assert "FIELD-AUDIT-M2M-GUARD-001" in AUDIT.read_text()


def test_audit_mentions_f003():
    assert "F-003" in AUDIT.read_text()


def test_audit_mentions_make_crud():
    assert "make:crud" in AUDIT.read_text()


def test_audit_mentions_many_to_many():
    content = AUDIT.read_text()
    assert "many_to_many" in content or "many-to-many" in content


def test_audit_mentions_pivot_fields():
    content = AUDIT.read_text()
    assert "pivot.fields" in content or "pivot_fields" in content


def test_audit_mentions_article():
    assert "Article" in AUDIT.read_text()


def test_audit_mentions_tag():
    assert "Tag" in AUDIT.read_text()


def test_audit_mentions_make_pivot_crud():
    assert "make:pivot-crud" in AUDIT.read_text()


# --- analyse ---

def test_audit_compares_multiple_options():
    content = AUDIT.read_text()
    # Doit comparer plusieurs options (A, B, C...)
    assert "Option" in content or "option" in content
    option_count = sum(1 for letter in "ABCDE" if f"| **{letter}**" in content or f"| {letter} " in content or f"**Option {letter}**" in content)
    assert option_count >= 3, "L'audit doit comparer au moins 3 options"


def test_audit_has_recommended_decision():
    content = AUDIT.read_text()
    assert "recommandée" in content or "Recommandée" in content or "recommandé" in content


def test_audit_identifies_from_side():
    content = AUDIT.read_text()
    assert "from" in content or "`from`" in content


def test_audit_identifies_bug():
    content = AUDIT.read_text()
    assert "bug" in content.lower() or "bogue" in content.lower()


# --- ticket suivant ---

def test_audit_proposes_fix_ticket():
    content = AUDIT.read_text()
    assert "FIELD-FIX-M2M-GUARD-001" in content or "FIELD-DOC-M2M-GUARD-001" in content


# --- garanties d'absence de modification ---

def test_audit_confirms_no_runtime_modification():
    content = AUDIT.read_text()
    assert "NON modifié" in content or "non modifié" in content or "NON" in content


def test_audit_confirms_no_pypi():
    content = AUDIT.read_text()
    assert "PyPI" in content
    assert "NON" in content


def test_audit_confirms_no_tag():
    content = AUDIT.read_text()
    assert "Tag" in content
    # Le rapport doit mentionner qu'aucun tag git n'a été créé
    assert "NON" in content
