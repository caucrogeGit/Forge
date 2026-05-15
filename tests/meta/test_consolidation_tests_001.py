"""Tests pour CONSOLIDATION-TESTS-001 — Audit couverture et zones fragiles des tests Forge."""

from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


def test_audit_consolidation_tests_001_existe():
    """docs/history/audits/consolidation-tests-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").exists()


def test_audit_mentionne_dossier_tests():
    """Le document d'audit mentionne tests/."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "tests/" in content or "tests\\" in content or "168 fichiers" in content


def test_audit_mentionne_core():
    """Le document d'audit mentionne le core."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "core" in content.lower()


def test_audit_mentionne_cli():
    """Le document d'audit mentionne la CLI."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "CLI" in content or "cli" in content.lower()


def test_audit_mentionne_auth_rbac():
    """Le document d'audit mentionne Auth/RBAC."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "auth" in content.lower() or "rbac" in content.lower()


def test_audit_mentionne_modules():
    """Le document d'audit mentionne les modules."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "module" in content.lower()


def test_audit_mentionne_profils():
    """Le document d'audit mentionne les profils."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "profil" in content.lower()


def test_audit_mentionne_starters():
    """Le document d'audit mentionne les starters."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "starter" in content.lower()


def test_audit_mentionne_non_ecrasement():
    """Le document d'audit mentionne le non-écrasement utilisateur."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "non-écrasement" in content.lower() or "overwrite" in content.lower() or "preserved" in content.lower()


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-tests-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_roadmap_marque_consolidation_tests_001_termine():
    """docs/forge-roadmap.md marque CONSOLIDATION-TESTS-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "CONSOLIDATION-TESTS-001" in content
    assert "terminé" in content


def test_roadmap_priorite_est_dans_phase_consolidation():
    """La prochaine priorité immédiate est un ticket CONSOLIDATION-*."""
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
