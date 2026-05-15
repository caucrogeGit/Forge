"""Tests — PHASE-13-CRUD-CLOSE-001 : clôture de la Phase 13.

Vérifie que :
- les 9 tickets Phase 13 sont présents et marqués livrés dans la roadmap ;
- PHASE-13-CRUD-CLOSE-001 est présent et livré ;
- la Phase 13 est marquée close ;
- la note de clôture mentionne les fonctionnalités consolidées ;
- la prochaine priorité est RELEASE-2.3.0-001 ;
- la documentation couvre les sujets clés.
"""
from __future__ import annotations

import pathlib

import pytest
pytestmark = pytest.mark.meta

ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")
REFERENCE = pathlib.Path("docs/reference/api.md")


def _roadmap() -> str:
    return ROADMAP.read_text(encoding="utf-8")


def _reference() -> str:
    return REFERENCE.read_text(encoding="utf-8")


def _livre(ticket: str) -> bool:
    r = _roadmap()
    start = 0
    while True:
        idx = r.find(ticket, start)
        if idx == -1:
            return False
        if "livré" in r[idx: idx + 80]:
            return True
        start = idx + 1


# ---------------------------------------------------------------------------
# Tickets Phase 13 livrés
# ---------------------------------------------------------------------------

class TestTicketsPhase13Livres:
    def test_crud_filter_001_livre(self):
        assert _livre("CRUD-FILTER-001")

    def test_crud_filter_htmx_001_livre(self):
        assert _livre("CRUD-FILTER-HTMX-001")

    def test_crud_filter_doc_001_livre(self):
        assert _livre("CRUD-FILTER-DOC-001")

    def test_crud_bulk_actions_audit_001_livre(self):
        assert _livre("CRUD-BULK-ACTIONS-AUDIT-001")

    def test_crud_bulk_delete_001_livre(self):
        assert _livre("CRUD-BULK-DELETE-001")

    def test_crud_sort_001_livre(self):
        assert _livre("CRUD-SORT-001")

    def test_crud_htmx_001_livre(self):
        assert _livre("CRUD-HTMX-001")

    def test_crud_export_audit_001_livre(self):
        assert _livre("CRUD-EXPORT-AUDIT-001")

    def test_crud_export_csv_001_livre(self):
        assert _livre("CRUD-EXPORT-CSV-001")

    def test_phase_13_close_001_livre(self):
        assert _livre("PHASE-13-CRUD-CLOSE-001")


# ---------------------------------------------------------------------------
# Clôture Phase 13
# ---------------------------------------------------------------------------

class TestCloturePhase13:
    def test_phase_13_mentionnee(self):
        assert "Phase 13" in _roadmap()

    def test_phase_13_close(self):
        r = _roadmap()
        assert "Phase 13" in r and "close" in r.lower()

    def test_note_cloture_presente(self):
        assert "Clôture Phase 13" in _roadmap()

    def test_phase_13_dans_section_close(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 13")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "Phase 13" in bloc


# ---------------------------------------------------------------------------
# Contenu de la note de clôture
# ---------------------------------------------------------------------------

class TestContenuCloture:
    def test_cloture_mentionne_filtres(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 13")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "filtre" in bloc.lower() or "list.filter" in bloc

    def test_cloture_mentionne_htmx(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 13")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "HTMX" in bloc or "htmx" in bloc.lower()

    def test_cloture_mentionne_tri(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 13")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "tri" in bloc.lower() or "sort" in bloc.lower()

    def test_cloture_mentionne_suppression_groupee(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 13")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "suppression" in bloc.lower() or "bulk" in bloc.lower()

    def test_cloture_mentionne_export_csv(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 13")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "export" in bloc.lower() or "CSV" in bloc


# ---------------------------------------------------------------------------
# Prochaine priorité
# ---------------------------------------------------------------------------

class TestProchainePriorite:
    def test_prochaine_priorite_forge_design(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc

    def test_release_2_3_0_livre(self):
        r = _roadmap()
        assert "RELEASE-2.3.0-001" in r and "livré" in r[r.find("RELEASE-2.3.0-001"): r.find("RELEASE-2.3.0-001") + 80]


# ---------------------------------------------------------------------------
# Documentation reference.md
# ---------------------------------------------------------------------------

class TestDocumentationReference:
    def test_reference_mentionne_list_filter(self):
        r = _reference()
        assert "list.filter" in r or "list_filter" in r or "filter" in r.lower()

    def test_reference_mentionne_htmx_crud(self):
        r = _reference()
        assert "HTMX" in r and "crud-results" in r

    def test_reference_mentionne_allowed_sort(self):
        r = _reference()
        assert "_ALLOWED_SORT" in r

    def test_reference_mentionne_suppression_groupee(self):
        r = _reference()
        assert "bulk" in r.lower() or "groupée" in r.lower()

    def test_reference_mentionne_export_csv(self):
        r = _reference()
        assert "export.csv" in r or "Export CSV" in r

    def test_reference_mentionne_export_limit(self):
        r = _reference()
        assert "_EXPORT_LIMIT" in r or "1000" in r

    def test_reference_mentionne_csv_escape(self):
        r = _reference()
        assert "_csv_escape" in r or "injection CSV" in r.lower()

    def test_reference_mentionne_cache_control(self):
        r = _reference()
        assert "Cache-Control" in r

    def test_reference_mentionne_rbac(self):
        r = _reference()
        assert "RBAC" in r or "require_permission" in r

    def test_reference_mentionne_csrf(self):
        r = _reference()
        assert "csrf" in r.lower() or "CSRF" in r
