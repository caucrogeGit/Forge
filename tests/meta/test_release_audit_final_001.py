"""Tests meta — RELEASE-AUDIT-001 : audit final post-RBAC et post-Pivot advanced.

Vérifie que le rapport d'audit final existe, couvre tous les domaines audités
et formule les bonnes conclusions.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT = Path("docs/history/audits/release-audit-final-post-rbac-pivot-001.md")


@pytest.fixture(scope="module")
def doc():
    assert AUDIT.exists(), f"{AUDIT} introuvable"
    return AUDIT.read_text(encoding="utf-8")


# ── Existence ─────────────────────────────────────────────────────────────────

def test_rapport_existe():
    assert AUDIT.exists()


# ── Identifiants du ticket ────────────────────────────────────────────────────

def test_mentionne_release_audit_001(doc):
    assert "RELEASE-AUDIT-001" in doc


# ── Domaines audités ──────────────────────────────────────────────────────────

def test_mentionne_rbac(doc):
    assert "RBAC" in doc


def test_mentionne_pivot_advanced(doc):
    assert "Pivot advanced" in doc or "pivot advanced" in doc.lower()


def test_mentionne_legacy_removal(doc):
    assert "legacy" in doc.lower() or "Legacy" in doc


def test_mentionne_json_schema(doc):
    assert "JSON Schema" in doc or "schema.json" in doc


# ── Commandes CLI vérifiées ───────────────────────────────────────────────────

def test_mentionne_rbac_validate(doc):
    assert "rbac:validate" in doc


def test_mentionne_rbac_audit(doc):
    assert "rbac:audit" in doc


def test_mentionne_make_pivot_crud(doc):
    assert "make:pivot-crud" in doc


def test_mentionne_pivot_advanced_service(doc):
    assert "PivotAdvancedService" in doc


# ── Invariants ────────────────────────────────────────────────────────────────

def test_mentionne_make_crud_neutre(doc):
    assert "make:crud" in doc
    assert "neutre" in doc


def test_mentionne_pytest_complet(doc):
    assert "pytest" in doc


def test_mentionne_mkdocs_strict(doc):
    assert "mkdocs build --strict" in doc or "mkdocs" in doc


# ── Garanties de non-publication ─────────────────────────────────────────────

def test_dit_aucune_publication_pypi(doc):
    lower = doc.lower()
    assert "publication pypi" in lower or "pypi" in lower
    assert "aucune publication pypi" in lower or "non effectuée" in lower or "non publié" in lower


def test_dit_aucun_tag_cree(doc):
    lower = doc.lower()
    assert "tag" in lower
    assert "non créé" in lower or "aucun tag" in lower or "non effectué" in lower


# ── Tickets suivants proposés ─────────────────────────────────────────────────

def test_propose_field_test_app_001(doc):
    assert "FIELD-TEST-APP-001" in doc


def test_propose_release_beta_next_001(doc):
    assert "RELEASE-BETA-NEXT-001" in doc


# ── Verdict ───────────────────────────────────────────────────────────────────

def test_verdict_audit_ok(doc):
    assert "AUDIT OK" in doc
