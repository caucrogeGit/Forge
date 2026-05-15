"""Tests pour PUBLICATION-2.0-VERSION-001 — Verrouillage version Forge 2.0.0."""

from __future__ import annotations

import json
import re
import tomllib
from pathlib import Path

import core

ROOT = Path(__file__).resolve().parents[2]

_EXPECTED = "1.0.0b1"
_EXPECTED_SEMVER = "1.0.0-beta.1"
_EXPECTED_REF = "v1.0.0-beta.1"


# ── Document d'audit ──────────────────────────────────────────────────────────

def test_audit_version_001_existe():
    """docs/history/audits/publication-2.0-version-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "publication-2.0-version-001.md").exists()


def test_audit_mentionne_forge_2_0():
    """Le document d'audit mentionne Forge 2.0.0."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-version-001.md").read_text(encoding="utf-8")
    assert "2.0.0" in content


def test_audit_contient_verdict():
    """Le document d'audit contient un verdict."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-version-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content or "VALIDÉ" in content


# ── Cohérence versions actives ────────────────────────────────────────────────

def test_pyproject_version_est_courante():
    """pyproject.toml déclare la version 2.0.0."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == _EXPECTED


def test_pyproject_classifier_est_stable_ou_beta():
    """pyproject.toml déclare un statut de maturité reconnu (Beta ou Stable)."""
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    classifiers = data["project"]["classifiers"]
    ACCEPTED = {"4 - Beta", "5 - Production/Stable"}
    assert any(any(s in c for s in ACCEPTED) for c in classifiers)


def test_core_version_est_courante():
    """core.__version__ est 2.0.0."""
    assert core.__version__ == _EXPECTED


def test_forge_py_version_est_courante():
    """forge.py déclare _FORGE_VERSION = "2.0.0"."""
    content = (ROOT / "forge.py").read_text(encoding="utf-8")
    assert re.search(rf'_FORGE_VERSION\s*=\s*"{re.escape(_EXPECTED)}"', content)


def test_forge_py_default_ref_est_courante():
    """forge.py déclare _FORGE_DEFAULT_REF = "v2.0.0"."""
    content = (ROOT / "forge.py").read_text(encoding="utf-8")
    assert re.search(rf'_FORGE_DEFAULT_REF\s*=\s*"{re.escape(_EXPECTED_REF)}"', content)


def test_package_json_version_est_courante():
    """package.json déclare la version SemVer courante."""
    data = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
    assert data["version"] == _EXPECTED_SEMVER


def test_versions_actives_sont_alignees():
    """pyproject.toml, core.__version__, forge.py et package.json sont tous à la version courante."""
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    forge_py = (ROOT / "forge.py").read_text(encoding="utf-8")
    package_json = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))

    assert pyproject["project"]["version"] == _EXPECTED
    assert core.__version__ == _EXPECTED
    assert re.search(rf'_FORGE_VERSION\s*=\s*"{re.escape(_EXPECTED)}"', forge_py)
    assert package_json["version"] == _EXPECTED_SEMVER


# ── Cohérence documentaire ────────────────────────────────────────────────────

def test_readme_titre_mentionne_version_3_0():
    """README.md titre contient la version courante."""
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert _EXPECTED_SEMVER in content.splitlines()[0]


def test_readme_git_clone_utilise_ref_3_0():
    """README.md git clone utilise le tag courant."""
    content = (ROOT / "README.md").read_text(encoding="utf-8")
    assert _EXPECTED_REF in content


def test_docs_index_html_mentionne_version_3_0():
    """docs/index.html affiche la version courante."""
    content = (ROOT / "docs" / "index.html").read_text(encoding="utf-8")
    assert _EXPECTED_REF in content or _EXPECTED in content


def test_docs_reference_mentionne_version_courante():
    """docs/reference.md mentionne la version courante ou son placeholder."""
    content = (ROOT / "docs" / "reference.md").read_text(encoding="utf-8")
    assert _EXPECTED in content or "{{forge_version}}" in content


def test_docs_installation_mentionne_version_courante():
    """docs/installation.md mentionne la version courante ou son placeholder."""
    content = (ROOT / "docs" / "installation.md").read_text(encoding="utf-8")
    assert _EXPECTED in content or "{{forge_version}}" in content


# ── CHANGELOG ─────────────────────────────────────────────────────────────────

def test_changelog_contient_section_2_0_0():
    """CHANGELOG.md contient une section ## 2.0.0."""
    content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## 2.0.0" in content


def test_changelog_preserve_section_1_5_0():
    """CHANGELOG.md conserve la section ## 1.5.0 (mention historique)."""
    content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    assert "## 1.5.0" in content


def test_changelog_section_2_0_0_avant_1_5_0():
    """Dans CHANGELOG.md, la section 2.0.0 précède la section 1.5.0."""
    content = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    idx_2 = content.find("## 2.0.0")
    idx_1 = content.find("## 1.5.0")
    assert idx_2 < idx_1


# ── Mentions historiques préservées ──────────────────────────────────────────

def test_roadmap_preserve_mention_v1_5_0():
    """docs/forge-roadmap.md conserve la mention v1.5.0 (tag historique)."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "v1.5.0" in content or "1.5.0" in content


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_marque_publication_2_0_version_001_termine():
    """docs/forge-roadmap.md marque PUBLICATION-2.0-VERSION-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "PUBLICATION-2.0-VERSION-001" in content
    assert "terminé" in content


def test_roadmap_indique_prochaine_priorite_publication():
    """docs/forge-roadmap.md indique un ticket POST-2.0 comme prochaine priorité."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    idx = content.find("Prochaine priorité immédiate")
    assert idx != -1
    bloc = content[idx: idx + 200]
    assert (
        "PUBLICATION-2.0-BUILD-001" in bloc
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
