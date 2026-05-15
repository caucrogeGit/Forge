"""Tests pour CONSOLIDATION-CLI-001 — Audit cohérence CLI Forge."""

from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


def test_audit_consolidation_cli_001_existe():
    """docs/history/audits/consolidation-cli-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-cli-001.md").exists()


def test_audit_mentionne_grandes_familles_commandes():
    """Le document d'audit couvre les grandes familles de commandes CLI."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-cli-001.md").read_text(encoding="utf-8")
    for famille in ("make:", "auth:", "module:", "starter:", "migration:", "mail:", "deploy:"):
        assert famille in content, f"Famille absente du document d'audit : {famille}"


def test_audit_mentionne_forge_new_profile():
    """Le document d'audit mentionne forge new --profile."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-cli-001.md").read_text(encoding="utf-8")
    assert "--profile" in content


def test_audit_mentionne_commandes_module():
    """Le document d'audit mentionne les commandes module:*."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-cli-001.md").read_text(encoding="utf-8")
    for cmd in ("module:list", "module:install", "module:files", "module:routes"):
        assert cmd in content, f"Commande absente : {cmd}"


def test_audit_mentionne_commandes_auth_user():
    """Le document d'audit mentionne les commandes auth:user:*."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-cli-001.md").read_text(encoding="utf-8")
    for cmd in ("auth:user:create", "auth:user:role:add", "auth:user:role:remove", "auth:user:roles"):
        assert cmd in content, f"Commande absente : {cmd}"


def test_roadmap_marque_consolidation_cli_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-CLI-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-CLI-001" in content
    assert "terminé" in content


def test_roadmap_priorite_est_dans_phase_consolidation():
    """La prochaine priorité immédiate dans la roadmap est un ticket CONSOLIDATION-*."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert "CONSOLIDATION-" in bloc or "PUBLICATION-" in bloc or "POST-2.0-" in bloc or "DEPENDENCY-" in bloc or "RELEASE-" in bloc or "CMD-" in bloc or "AUTH-LEGACY-" in bloc or "CRUD-" in bloc or "SESSION-" in bloc or "I18N-" in bloc or "QUALITY-" in bloc or "RELEASE-2.1" in bloc or "SESSION-STORE-" in bloc or "SECURITY-" in bloc or "MODULE-" in bloc or "PROFILE-" in bloc or "HTTP-" in bloc or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-OIDC-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc


def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été supprimé."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()
