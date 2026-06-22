"""Tests pour PUBLICATION-2.0-PREP-001 — Préparation publication Forge 2.0."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


# ── Document d'audit ──────────────────────────────────────────────────────────

def test_audit_publication_2_0_prep_001_existe():
    """docs/history/audits/publication-2.0-prep-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").exists()


def test_audit_mentionne_forge_2_0():
    """Le document d'audit mentionne Forge 2.0."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "Forge 2.0" in content


def test_audit_mentionne_pyproject_toml():
    """Le document d'audit mentionne pyproject.toml."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "pyproject.toml" in content


def test_audit_mentionne_readme():
    """Le document d'audit mentionne README.md."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "README" in content


def test_audit_mentionne_python_m_build():
    """Le document d'audit mentionne la commande de build du paquet."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "python -m build" in content


def test_audit_mentionne_forge_version():
    """Le document d'audit mentionne forge --version."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "forge --version" in content


def test_audit_mentionne_limites_assumees():
    """Le document d'audit mentionne les limites assumées."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "limite" in content.lower() or "Limite" in content


def test_audit_clarifie_oidc_admin():
    """Le document d'audit clarifie le statut OIDC et admin utilisateurs."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "OIDC" in content
    assert "admin" in content.lower()
    assert "livré" in content.lower() or "terminé" in content.lower()


def test_audit_contient_verdict_final():
    """Le document d'audit contient un verdict final."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content


def test_audit_contient_checklist_publication():
    """Le document d'audit contient une checklist de publication."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-prep-001.md").read_text(encoding="utf-8")
    assert "checklist" in content.lower() or "Checklist" in content


# ── Cohérence packaging ───────────────────────────────────────────────────────

def test_pyproject_toml_existe():
    """pyproject.toml existe à la racine."""
    assert (ROOT / "pyproject.toml").exists()


def test_pyproject_toml_declare_forge_mvc():
    """pyproject.toml déclare le projet forge-mvc."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge-mvc" in content


def test_pyproject_toml_inclut_core():
    """pyproject.toml inclut le package core dans le wheel."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "core" in content


def test_pyproject_toml_inclut_cli():
    """pyproject.toml inclut le package cli dans le wheel."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "cli" in content


def test_pyproject_toml_declare_script_forge():
    """pyproject.toml déclare le script CLI forge."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "forge" in content
    assert "cli_entrypoint" in content


def test_license_existe():
    """LICENSE existe à la racine."""
    assert (ROOT / "LICENSE").exists()


def test_changelog_existe():
    """CHANGELOG.md existe à la racine."""
    assert (ROOT / "CHANGELOG.md").exists()


# ── OIDC / admin livré en Phase 4.5 ──────────────────────────────────────────

def test_roadmap_auth_oidc_001_termine():
    """docs/forge-roadmap.md marque AUTH-OIDC-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "AUTH-OIDC-001" in content
    idx = content.find("AUTH-OIDC-001")
    assert "terminé" in content[idx: idx + 60]


def test_roadmap_auth_admin_001_termine():
    """docs/forge-roadmap.md marque AUTH-ADMIN-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "AUTH-ADMIN-001" in content
    idx = content.find("AUTH-ADMIN-001")
    assert "terminé" in content[idx: idx + 60]


def test_consolidation_roadmap_ne_liste_plus_oidc_comme_non_livre():
    """docs/history/audits/consolidation-roadmap-001.md ne liste plus OIDC comme post-2.0 non livré."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "Tickets AUTH-OIDC-001 à 003 planifiés" not in content


def test_consolidation_roadmap_indique_oidc_livre():
    """docs/history/audits/consolidation-roadmap-001.md indique OIDC comme livré en Phase 4.5."""
    content = (ROOT / "docs" / "history" / "audits" / "consolidation-roadmap-001.md").read_text(encoding="utf-8")
    assert "livré" in content.lower() or "terminé" in content.lower()


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_marque_publication_2_0_prep_001_termine():
    """docs/forge-roadmap.md marque PUBLICATION-2.0-PREP-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "PUBLICATION-2.0-PREP-001" in content
    assert "terminé" in content


def test_roadmap_indique_prochaine_priorite_publication():
    """docs/forge-roadmap.md indique un ticket PUBLICATION-2.0 comme prochaine priorité."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert (
        "PUBLICATION-2.0-VERSION-001" in bloc
        or "PUBLICATION-2.0-BUILD-001" in bloc
        or "PUBLICATION-2.0-TAG-001" in bloc
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
