"""Tests meta — PIVOT-ADVANCED-008 : documentation complète Pivot advanced.

Vérifie que la page docs/entities/pivot-advanced.md existe, couvre toutes
les APIs et limites, et que mkdocs.yml et pivots-many-to-many.md la référencent.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

# Doc embarquée par paquet depuis l'ADR-038 (montée sous /pivot/reference/).
# Référence éclatée en pages par-module (DOCS-PIVOT-REFERENCE-SPLIT-001) :
# index + references/*.md. Le contenu est vérifié sur l'ensemble agrégé.
DOC_DIR = Path("packages/forge-mvc-pivot/docs")
DOC_PAGE = DOC_DIR / "reference.md"
MKDOCS = Path("mkdocs.yml")
PIVOTS_PAGE = Path("docs/entities/pivots-many-to-many.md")
AUDIT_001 = Path("docs/history/audits/pivot-advanced-functional-model-001.md")


@pytest.fixture(scope="module")
def doc():
    assert DOC_PAGE.exists(), f"{DOC_PAGE} introuvable"
    # Agrège l'index et les pages par-module : le contenu de référence est
    # désormais réparti (service.md, make_pivot_crud.md), pas dans un seul fichier.
    parts = [DOC_PAGE.read_text(encoding="utf-8")]
    refs = DOC_DIR / "references"
    parts += [p.read_text(encoding="utf-8") for p in sorted(refs.glob("*.md"))]
    return "\n".join(parts)


@pytest.fixture(scope="module")
def mkdocs():
    return MKDOCS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def pivots_page():
    return PIVOTS_PAGE.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def audit_001():
    return AUDIT_001.read_text(encoding="utf-8")


# ── Existence et titre ────────────────────────────────────────────────────────

def test_page_pivot_advanced_existe():
    assert DOC_PAGE.exists()


def test_page_mentionne_pivot_advanced(doc):
    assert "Pivot advanced" in doc or "pivot advanced" in doc.lower()


# ── Contrat relations.json ────────────────────────────────────────────────────

def test_page_mentionne_pivot_fields(doc):
    assert "pivot.fields" in doc


def test_page_mentionne_article_tag(doc):
    assert "article_tag" in doc


def test_page_mentionne_article_tag_relation(doc):
    assert "Article" in doc and "Tag" in doc


# ── Commande make:pivot-crud ──────────────────────────────────────────────────

def test_page_mentionne_make_pivot_crud(doc):
    assert "make:pivot-crud" in doc


def test_page_mentionne_dry_run(doc):
    assert "--dry-run" in doc


def test_page_mentionne_routes_non_branchees_automatiquement(doc):
    assert "automatiquement" in doc
    assert "routes" in doc.lower()


# ── PivotAdvancedService ──────────────────────────────────────────────────────

def test_page_mentionne_pivot_advanced_service(doc):
    assert "PivotAdvancedService" in doc


def test_page_mentionne_attach(doc):
    assert "attach" in doc


def test_page_mentionne_update(doc):
    assert "update" in doc


def test_page_mentionne_detach(doc):
    assert "detach" in doc


def test_page_mentionne_list_for_source(doc):
    assert "list_for_source" in doc


def test_page_mentionne_get(doc):
    assert "service.get(" in doc or ".get(" in doc


# ── Contraintes ───────────────────────────────────────────────────────────────

def test_page_mentionne_pivot_field_constraint(doc):
    assert "PivotFieldConstraint" in doc


def test_page_mentionne_required(doc):
    assert "required" in doc


def test_page_mentionne_nullable(doc):
    assert "nullable" in doc


def test_page_mentionne_unique_pair(doc):
    assert "unique_pair" in doc


def test_page_mentionne_id_field(doc):
    assert "id_field" in doc


# ── Erreurs UX ────────────────────────────────────────────────────────────────

def test_page_mentionne_pivot_constraint_error(doc):
    assert "PivotConstraintError" in doc


def test_page_mentionne_pivot_form_error(doc):
    assert "PivotFormError" in doc


def test_page_mentionne_pivot_error_to_form_error(doc):
    assert "pivot_error_to_form_error" in doc


def test_page_mentionne_codes_erreur(doc):
    assert "required_field_missing" in doc
    assert "nullable_field_rejected" in doc
    assert "duplicate_pair" in doc
    assert "missing_id_field" in doc
    assert "unknown_pivot_field" in doc
    assert "invalid_pivot_data" in doc


# ── Limites ───────────────────────────────────────────────────────────────────

def test_page_dit_make_crud_reste_neutre(doc):
    assert "make:crud" in doc
    assert "neutre" in doc


def test_page_dit_routes_non_branchees(doc):
    assert "automatiquement" in doc


def test_page_ne_dit_pas_pypi_publie(doc):
    lower = doc.lower()
    assert "pypi" not in lower
    assert "publié sur pypi" not in lower
    assert "forge-mvc publié" not in lower


# ── mkdocs.yml ────────────────────────────────────────────────────────────────

def test_mkdocs_reference_la_page(mkdocs):
    # Doc embarquée (ADR-038) : le site agrège le sous-mkdocs du paquet pivot.
    assert "packages/forge-mvc-pivot/mkdocs.yml" in mkdocs


# ── pivots-many-to-many.md ────────────────────────────────────────────────────

def test_pivots_page_contient_lien_vers_pivot_advanced(pivots_page):
    # Lien vers la référence pivot embarquée (ADR-038).
    assert "../pivot/reference.md" in pivots_page


# ── Audit ─────────────────────────────────────────────────────────────────────

def test_audit_mentionne_pivot_advanced_008(audit_001):
    assert "PIVOT-ADVANCED-008" in audit_001
