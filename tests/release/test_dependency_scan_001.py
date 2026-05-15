"""Tests pour DEPENDENCY-SCAN-001 — Contrôle des dépendances avec pip-audit."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_requirements_txt_existe():
    """requirements.txt existe à la racine du dépôt."""
    assert (ROOT / "requirements.txt").exists()


def test_requirements_dev_txt_existe():
    """requirements-dev.txt existe à la racine du dépôt."""
    assert (ROOT / "requirements-dev.txt").exists()


def test_pip_audit_dans_requirements_dev():
    """requirements-dev.txt référence pip-audit."""
    content = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "pip-audit" in content


def test_workflow_dependency_audit_existe():
    """.github/workflows/dependency-audit.yml existe."""
    assert (ROOT / ".github" / "workflows" / "dependency-audit.yml").exists()


def test_workflow_dependency_audit_contient_pip_audit():
    """.github/workflows/dependency-audit.yml référence pip-audit."""
    content = (ROOT / ".github" / "workflows" / "dependency-audit.yml").read_text(
        encoding="utf-8"
    )
    assert "pip-audit" in content


def test_workflow_dependency_audit_non_bloquant():
    """.github/workflows/dependency-audit.yml utilise continue-on-error."""
    content = (ROOT / ".github" / "workflows" / "dependency-audit.yml").read_text(
        encoding="utf-8"
    )
    assert "continue-on-error" in content


def test_workflow_dependency_audit_planifie():
    """.github/workflows/dependency-audit.yml a un déclencheur schedule."""
    content = (ROOT / ".github" / "workflows" / "dependency-audit.yml").read_text(
        encoding="utf-8"
    )
    assert "schedule" in content


def test_security_md_mentionne_pip_audit():
    """SECURITY.md documente pip-audit."""
    content = (ROOT / "SECURITY.md").read_text(encoding="utf-8")
    assert "pip-audit" in content


def test_roadmap_reference_dependency_scan_001():
    """forge-roadmap.md référence DEPENDENCY-SCAN-001."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(
        encoding="utf-8"
    )
    assert "DEPENDENCY-SCAN-001" in content
