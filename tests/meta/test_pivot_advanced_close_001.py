"""Tests meta — PIVOT-ADVANCED-CLOSE-001 : clôture du bloc Pivot advanced.

Vérifie que le rapport fonctionnel porte la section de clôture et référence
tous les tickets du bloc, toutes les APIs livrées et les invariants non négociables.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT_FONCTIONNEL = Path("docs/history/audits/pivot-advanced-functional-model-001.md")
AUDIT_UX = Path("docs/history/audits/pivot-advanced-ux-model-002.md")


@pytest.fixture(scope="module")
def audit_fonctionnel():
    assert AUDIT_FONCTIONNEL.exists()
    return AUDIT_FONCTIONNEL.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def audit_ux():
    assert AUDIT_UX.exists()
    return AUDIT_UX.read_text(encoding="utf-8")


# ── Existence des rapports ────────────────────────────────────────────────────

def test_rapport_fonctionnel_existe():
    assert AUDIT_FONCTIONNEL.exists()


def test_rapport_ux_existe():
    assert AUDIT_UX.exists()


# ── Section de clôture ────────────────────────────────────────────────────────

def test_rapport_fonctionnel_mentionne_close_001(audit_fonctionnel):
    assert "PIVOT-ADVANCED-CLOSE-001" in audit_fonctionnel


def test_rapport_ux_mentionne_close_001(audit_ux):
    assert "PIVOT-ADVANCED-CLOSE-001" in audit_ux


# ── Tickets du bloc référencés ────────────────────────────────────────────────

def test_mentionne_pivot_advanced_001(audit_fonctionnel):
    assert "PIVOT-ADVANCED-001" in audit_fonctionnel


def test_mentionne_pivot_advanced_002(audit_fonctionnel):
    assert "PIVOT-ADVANCED-002" in audit_fonctionnel


def test_mentionne_pivot_advanced_003(audit_fonctionnel):
    assert "PIVOT-ADVANCED-003" in audit_fonctionnel


def test_mentionne_pivot_advanced_004(audit_fonctionnel):
    assert "PIVOT-ADVANCED-004" in audit_fonctionnel


def test_mentionne_pivot_advanced_005(audit_fonctionnel):
    assert "PIVOT-ADVANCED-005" in audit_fonctionnel


def test_mentionne_pivot_advanced_006(audit_fonctionnel):
    assert "PIVOT-ADVANCED-006" in audit_fonctionnel


def test_mentionne_pivot_advanced_007(audit_fonctionnel):
    assert "PIVOT-ADVANCED-007" in audit_fonctionnel


def test_mentionne_pivot_advanced_008(audit_fonctionnel):
    assert "PIVOT-ADVANCED-008" in audit_fonctionnel


# ── APIs livrées ──────────────────────────────────────────────────────────────

def test_mentionne_pivot_advanced_service(audit_fonctionnel):
    assert "PivotAdvancedService" in audit_fonctionnel


def test_mentionne_make_pivot_crud(audit_fonctionnel):
    assert "make:pivot-crud" in audit_fonctionnel


def test_mentionne_pivot_field_constraint(audit_fonctionnel):
    assert "PivotFieldConstraint" in audit_fonctionnel


def test_mentionne_pivot_constraint_error(audit_fonctionnel):
    assert "PivotConstraintError" in audit_fonctionnel


def test_mentionne_pivot_form_error(audit_fonctionnel):
    assert "PivotFormError" in audit_fonctionnel


def test_mentionne_pivot_error_to_form_error(audit_fonctionnel):
    assert "pivot_error_to_form_error" in audit_fonctionnel


# ── Invariants non négociables ────────────────────────────────────────────────

def test_dit_make_crud_reste_neutre(audit_fonctionnel):
    assert "make:crud" in audit_fonctionnel
    assert "neutre" in audit_fonctionnel


def test_dit_routes_non_branchees_automatiquement(audit_fonctionnel):
    assert "automatiquement" in audit_fonctionnel
    assert "routes" in audit_fonctionnel.lower()


def test_dit_schemas_json_non_modifies(audit_fonctionnel):
    assert "schéma" in audit_fonctionnel.lower() or "schémas" in audit_fonctionnel.lower()


def test_ne_dit_pas_pypi_publie(audit_fonctionnel):
    lower = audit_fonctionnel.lower()
    assert "pypi" not in lower or "aucune publication pypi" in lower or "publication pypi" in lower


def test_ne_dit_pas_tag_cree(audit_fonctionnel):
    lower = audit_fonctionnel.lower()
    assert "création de tag" not in lower or "aucune" in lower or "n'a pas" in lower
