"""Tests pour PUBLICATION-2.0-BUILD-001 — Build package Forge 2.0."""

from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.docs

ROOT = Path(__file__).resolve().parents[2]


# ── Document d'audit ──────────────────────────────────────────────────────────

def test_audit_build_001_existe():
    """docs/history/audits/publication-2.0-build-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").exists()


def test_audit_mentionne_python_m_build():
    """Le document d'audit mentionne python -m build."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").read_text(encoding="utf-8")
    assert "python -m build" in content


def test_audit_mentionne_wheel_2_0_0():
    """Le document d'audit mentionne le wheel forge_mvc-2.0.0."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").read_text(encoding="utf-8")
    assert "2.0.0" in content
    assert "whl" in content


def test_audit_mentionne_forge_version():
    """Le document d'audit mentionne forge --version."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").read_text(encoding="utf-8")
    assert "forge --version" in content


def test_audit_mentionne_forge_starter_list():
    """Le document d'audit mentionne forge starter:list."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").read_text(encoding="utf-8")
    assert "forge starter:list" in content


def test_audit_mentionne_absence_tag():
    """Le document d'audit mentionne l'absence de tag."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").read_text(encoding="utf-8")
    assert "tag" in content.lower()
    assert "v2.0.0" in content


def test_audit_contient_verdict():
    """Le document d'audit contient un verdict."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-build-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content or "VALIDÉ" in content


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_marque_publication_2_0_build_001_termine():
    """docs/forge-roadmap.md marque PUBLICATION-2.0-BUILD-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "PUBLICATION-2.0-BUILD-001" in content
    idx = content.find("PUBLICATION-2.0-BUILD-001")
    assert "terminé" in content[idx: idx + 80]


def test_roadmap_indique_prochaine_priorite_publication():
    """docs/forge-roadmap.md indique un ticket PUBLICATION-2.0 comme prochaine priorité."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert (
        "PUBLICATION-2.0-TAG-001" in bloc
        or "PUBLICATION-2.0-RELEASE-001" in bloc
        or "POST-2.0-ROADMAP-001" in bloc
        or "POST-2.0-DOC-CLEANUP-001" in bloc
        or "POST-2.0-ROADMAP-RESTRUCTURE-001" in bloc
        or "DEPENDENCY-SCAN-001" in bloc
        or "RELEASE-CHECKLIST-001" in bloc
        or "CMD-LEGACY-DEPRECATION-001" in bloc
        or "AUTH-LEGACY-BOUNDARY-001" in bloc
        or "CRUD-GENERATOR-SPLIT-001" in bloc
        or "SESSION-STORE-CONTRACT-001" in bloc
        or "I18N-CACHE-001" in bloc
        or "QUALITY-RUFF-001" in bloc
        or "RELEASE-2.1.0-001" in bloc
        or "SESSION-STORE-CONTRACT-001" in bloc
        or "SESSION-FILE-STORE-001" in bloc
        or "SESSION-MARIADB-STORE-001" in bloc
        or "SECURITY-CSP-NONCE-001" in bloc
        or "SECURITY-TLS-" in bloc
        or "SECURITY-COOKIES-" in bloc
        or "SECURITY-HEADERS-" in bloc
        or "SECURITY-UPLOADS-" in bloc
        or "SECURITY-UPLOAD-" in bloc
        or "SECURITY-RBAC-" in bloc
        or "SECURITY-CACHE-" in bloc
        or "DEPLOY-PROD-SECURITY-DOC-" in bloc
        or "DEPLOY-PROD-" in bloc
        or "MODULE-LIFECYCLE-" in bloc
        or "MODULE-REMOVE-" in bloc
        or "PROFILE-DIFFERENTIATION-" in bloc
        or "HTTP-" in bloc
        or "CONCURRENCY-" in bloc or "HEALTH-" in bloc or "RELEASE-" in bloc or "APP-" in bloc or "DX-" in bloc or "HELP-" in bloc or "RECOVERY-" in bloc or "AUDIT-" in bloc or "E2E-" in bloc or "DOC-" in bloc or "API-" in bloc or "AUTH-MFA-" in bloc or "AUTH-SESSION-" in bloc or "AUTH-ADMIN-" in bloc or "AUTH-DOC-" in bloc or "PHASE-" in bloc or "CRUD-" in bloc or "ROADMAP-" in bloc or "POST-" in bloc or "WORKFLOW-" in bloc
    )


# ── Gardes ────────────────────────────────────────────────────────────────────

def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été modifié."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()
