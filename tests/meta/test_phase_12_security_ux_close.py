"""Tests — PHASE-12-SECURITY-UX-CLOSE-001 : clôture de la Phase 12.

Vérifie que :
- les 5 tickets Phase 12 sont présents et marqués livrés dans la roadmap ;
- PHASE-12-SECURITY-UX-CLOSE-001 est présent et livré ;
- la Phase 12 est marquée close ;
- la prochaine priorité est CRUD-FILTER-001 ;
- la documentation production mentionne les livrables clés.
"""
from __future__ import annotations

import pathlib

import pytest
pytestmark = pytest.mark.meta

ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")
PROD_MD = pathlib.Path("docs/production-security.md")


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


def _prod():
    return PROD_MD.read_text(encoding="utf-8")


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
# Tickets Phase 12 livrés
# ---------------------------------------------------------------------------

class TestTicketsPhase12Livres:
    def test_crud_rbac_ui_001_livre(self):
        assert _livre("CRUD-RBAC-UI-001")

    def test_security_cache_001_livre(self):
        assert _livre("SECURITY-CACHE-001")

    def test_security_cookies_host_prefix_001_livre(self):
        assert _livre("SECURITY-COOKIES-HOST-PREFIX-001")

    def test_e2e_upload_http_001_livre(self):
        assert _livre("E2E-UPLOAD-HTTP-001")

    def test_security_upload_rate_limit_001_livre(self):
        assert _livre("SECURITY-UPLOAD-RATE-LIMIT-001")

    def test_phase_12_close_001_livre(self):
        assert _livre("PHASE-12-SECURITY-UX-CLOSE-001")


# ---------------------------------------------------------------------------
# Clôture Phase 12
# ---------------------------------------------------------------------------

class TestCloturePhase12:
    def test_phase_12_mentionnee(self):
        r = _roadmap()
        assert "Phase 12" in r

    def test_phase_12_close_mentionnee(self):
        r = _roadmap()
        assert "Phase 12" in r and "close" in r.lower()

    def test_note_cloture_phase_12_presente(self):
        r = _roadmap()
        assert "Clôture Phase 12" in r

    def test_phase_12_dans_conclusion(self):
        r = _roadmap()
        # Phase 12 doit être mentionnée dans la roadmap (résumé de clôture)
        assert "Phase 12" in r


# ---------------------------------------------------------------------------
# Contenu de la note de clôture
# ---------------------------------------------------------------------------

class TestContenuCloture:
    def test_cloture_mentionne_rbac_ui(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 12")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "can(" in bloc or "RBAC" in bloc or "permission" in bloc.lower()

    def test_cloture_mentionne_cache_control(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 12")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "Cache-Control" in bloc or "no-store" in bloc

    def test_cloture_mentionne_host_prefix(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 12")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "__Host-" in bloc

    def test_cloture_mentionne_upload_multipart(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 12")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "upload" in bloc.lower() or "multipart" in bloc.lower()

    def test_cloture_mentionne_rate_limit(self):
        r = _roadmap()
        idx = r.find("Clôture Phase 12")
        assert idx != -1
        bloc = r[idx: idx + 600]
        assert "rate limit" in bloc.lower() or "rate_limit" in bloc


# ---------------------------------------------------------------------------
# Prochaine priorité
# ---------------------------------------------------------------------------

class TestProchainePriorite:
    def test_prochaine_priorite_workflow_statuts(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        assert idx != -1
        bloc = r[idx: idx + 200]
        assert "FORGE-DESIGN-ROADMAP-001" in bloc


# ---------------------------------------------------------------------------
# Documentation production cohérente
# ---------------------------------------------------------------------------

class TestDocumentationProduction:
    def test_prod_mentionne_cookie_host_prefix(self):
        assert "__Host-" in _prod()

    def test_prod_mentionne_cache_control(self):
        assert "Cache-Control" in _prod() or "no-store" in _prod()

    def test_prod_mentionne_rate_limit_upload(self):
        p = _prod()
        assert "rate_limit" in p or "rate limit" in p.lower()

    def test_prod_mentionne_upload_e2e(self):
        assert "E2E-UPLOAD-HTTP-001" in _prod() or "quasi-E2E" in _prod()

    def test_prod_security_upload_rate_limit_livre(self):
        p = _prod()
        assert "SECURITY-UPLOAD-RATE-LIMIT-001" in p
        idx = p.index("SECURITY-UPLOAD-RATE-LIMIT-001")
        assert "livré" in p[idx: idx + 80]
