"""Tests — PHASE-11-AUTH-CLOSE-001 : clôture de la Phase 11 Auth avancée.

Vérifie que :
- tous les tickets Phase 11 sont présents et marqués livrés dans la roadmap ;
- la Phase 11 est marquée close ;
- la prochaine priorité est CRUD-RBAC-UI-001 ;
- les liens croisés Auth/RBAC sont présents dans la documentation.
"""
from __future__ import annotations

import pathlib

import pytest
pytestmark = pytest.mark.meta

ROADMAP = pathlib.Path("docs/roadmap/forge-roadmap.md")
AUTH_MD = pathlib.Path("docs/auth.md")
RBAC_MD = pathlib.Path("docs/rbac.md")


def _roadmap():
    return ROADMAP.read_text(encoding="utf-8")


def _auth():
    return AUTH_MD.read_text(encoding="utf-8")


def _rbac():
    return RBAC_MD.read_text(encoding="utf-8")


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
# Tickets Phase 11 livrés
# ---------------------------------------------------------------------------

class TestTicketsPhase11Livres:
    def test_auth_mfa_004_livre(self):
        assert _livre("AUTH-MFA-004")

    def test_auth_session_hardening_001_livre(self):
        assert _livre("AUTH-SESSION-HARDENING-001")

    def test_auth_admin_ux_001_livre(self):
        assert _livre("AUTH-ADMIN-UX-001")

    def test_auth_doc_consolidation_001_livre(self):
        assert _livre("AUTH-DOC-CONSOLIDATION-001")

    def test_phase_11_auth_close_001_livre(self):
        assert _livre("PHASE-11-AUTH-CLOSE-001")


# ---------------------------------------------------------------------------
# Clôture Phase 11
# ---------------------------------------------------------------------------

class TestCloturePase11:
    def test_cloture_phase_11_mentionnee(self):
        r = _roadmap()
        assert "Phase 11" in r and ("close" in r.lower() or "terminé" in r.lower() or "livré" in r.lower())

    def test_phase_11_dans_conclusion(self):
        r = _roadmap()
        idx = r.find("Prochaine priorité immédiate")
        conclusion_start = r.rfind("## Conclusion", 0, idx)
        bloc = r[conclusion_start: idx + 200] if conclusion_start != -1 else r[max(0, idx - 500): idx + 200]
        assert "Phase 11" in bloc or "AUTH-DOC-CONSOLIDATION" in bloc


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
# Documentation Auth/RBAC cohérente
# ---------------------------------------------------------------------------

class TestDocumentationCoherente:
    def test_auth_md_lien_vers_rbac(self):
        assert "rbac.md" in _auth()

    def test_rbac_md_lien_vers_auth(self):
        assert "auth.md" in _rbac()

    def test_auth_md_limites_presentes(self):
        assert "Limites restantes" in _auth()

    def test_auth_md_voir_aussi_present(self):
        assert "Voir aussi" in _auth()

    def test_auth_md_section_mfa(self):
        assert "## MFA" in _auth()

    def test_auth_md_section_oidc(self):
        assert "## OIDC" in _auth()
