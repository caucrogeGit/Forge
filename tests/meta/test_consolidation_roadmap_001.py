"""Tests pour CONSOLIDATION-ROADMAP-001 — Décision Forge 2.0, Forge Design et post-roadmap."""

from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ── Document d'audit ──────────────────────────────────────────────────────────

def test_audit_consolidation_roadmap_001_existe():
    """docs/history/audits/consolidation-roadmap-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").exists()


def test_audit_mentionne_forge_2_0():
    """Le document d'audit mentionne Forge 2.0."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "Forge 2.0" in content


def test_audit_mentionne_forge_design():
    """Le document d'audit mentionne Forge Design."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "Forge Design" in content


def test_audit_mentionne_post_2_0():
    """Le document d'audit mentionne les éléments post-2.0."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "post-2.0" in content.lower() or "Post-2.0" in content


def test_audit_mentionne_limites_assumees():
    """Le document d'audit mentionne les limites assumées."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "limite" in content.lower() or "Limite" in content


def test_audit_mentionne_communes_sejours_demonstrateur():
    """Le document d'audit confirme Communes & Séjours comme démonstrateur."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "Communes" in content
    assert "démonstrateur" in content.lower()


def test_audit_mentionne_paiement_exclu():
    """Le document d'audit exclut le paiement du cœur Forge."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "paiement" in content.lower()


def test_audit_mentionne_saas_exclu():
    """Le document d'audit exclut le SaaS multi-tenant du cœur Forge."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "SaaS" in content or "multi-tenant" in content.lower()


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_audit_contient_tableau_synthese():
    """Le document d'audit contient un tableau de synthèse des décisions."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "Forge 2.0" in content
    assert "Projet séparé" in content or "séparé" in content.lower()
    assert "Exclu" in content


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_marque_consolidation_roadmap_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-ROADMAP-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-ROADMAP-001" in content
    assert "terminé" in content


def test_roadmap_indique_phase_9_5_terminee():
    """docs/forge-roadmap.md indique que la Phase 9.5 est terminée."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "Phase 9.5" in content
    assert "terminée" in content or "close" in content or "terminé" in content


def test_roadmap_indique_prochaine_priorite_publication():
    """docs/forge-roadmap.md indique une prochaine priorité liée à la publication."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert "PUBLICATION-" in bloc or "RELEASE-" in bloc or "POST-2.0-" in bloc or "DEPENDENCY-" in bloc or "CMD-" in bloc or "AUTH-LEGACY-" in bloc or "CRUD-" in bloc or "SESSION-" in bloc or "I18N-" in bloc or "QUALITY-" in bloc or "RELEASE-2.1" in bloc or "SESSION-STORE-" in bloc or "SECURITY-" in bloc or "MODULE-" in bloc or "PROFILE-" in bloc or "HTTP-" in bloc or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-OIDC-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc


def test_roadmap_mentionne_forge_design_separe():
    """docs/forge-roadmap.md mentionne Forge Design comme projet séparé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "Forge Design" in content
    assert "séparé" in content.lower() or "compagnon" in content.lower()


# ── Gardes ────────────────────────────────────────────────────────────────────

def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été modifié."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()


def test_aucun_element_paiement_dans_core():
    """core/ ne contient pas de référence à un système de paiement intégré."""
    for f in (ROOT / "core").rglob("*.py"):
        content = f.read_text(encoding="utf-8").lower()
        assert "stripe" not in content, f"Référence Stripe dans {f}"
        assert "paypal" not in content, f"Référence PayPal dans {f}"


def test_aucun_element_saas_dans_core():
    """core/ ne contient pas de logique SaaS multi-tenant."""
    for f in (ROOT / "core").rglob("*.py"):
        content = f.read_text(encoding="utf-8").lower()
        assert "multi_tenant" not in content, f"Logique multi-tenant dans {f}"
        assert "tenant_id" not in content, f"tenant_id dans {f}"
