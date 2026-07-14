"""Tests pour PUBLICATION-2.0-POST-RELEASE-001 — Post-release Forge 2.0.0."""

from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.docs

ROOT = Path(__file__).resolve().parents[2]

_RELEASE_URL = "https://github.com/caucrogeGit/Forge/releases/tag/v2.0.0"


# ── Document d'audit ──────────────────────────────────────────────────────────

def test_audit_post_release_001_existe():
    """docs/history/audits/publication-2.0-post-release-001.md existe."""
    assert (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").exists()


def test_audit_mentionne_forge_2_0_0():
    """Le document d'audit mentionne Forge 2.0.0."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert "Forge 2.0.0" in content


def test_audit_mentionne_tag_v2_0_0():
    """Le document d'audit mentionne v2.0.0."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert "v2.0.0" in content


def test_audit_mentionne_url_release_github():
    """Le document d'audit mentionne l'URL de la release GitHub."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert _RELEASE_URL in content


def test_audit_mentionne_wheel():
    """Le document d'audit mentionne le wheel."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert "whl" in content


def test_audit_mentionne_sdist():
    """Le document d'audit mentionne le sdist."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert "tar.gz" in content


def test_audit_confirme_pas_de_publication_pypi():
    """Le document d'audit confirme que PyPI n'a pas été publié."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert "PyPI" in content


def test_audit_contient_verdict():
    """Le document d'audit contient un verdict."""
    content = (ROOT / "docs" / "history" / "audits" / "publication-2.0-post-release-001.md").read_text(encoding="utf-8")
    assert "Verdict" in content or "VALIDÉ" in content


# ── Roadmap ───────────────────────────────────────────────────────────────────

def test_roadmap_marque_post_release_001_termine():
    """docs/forge-roadmap.md marque PUBLICATION-2.0-POST-RELEASE-001 comme terminé."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "PUBLICATION-2.0-POST-RELEASE-001" in content
    idx = content.find("PUBLICATION-2.0-POST-RELEASE-001")
    assert "terminé" in content[idx: idx + 80]


def test_roadmap_mentionne_release_github():
    """docs/forge-roadmap.md mentionne la release GitHub Forge 2.0.0."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "releases/tag/v2.0.0" in content or _RELEASE_URL in content


# ── Gardes ────────────────────────────────────────────────────────────────────

def test_roadmap_md_non_recree():
    """docs/roadmap.md ne doit pas exister."""
    assert not (ROOT / "docs" / "roadmap.md").exists()


def test_forge_design_roadmap_non_modifie():
    """docs/forge-design-roadmap.md existe et n'a pas été modifié."""
    assert (ROOT / "docs" / "roadmap" / "forge-design-roadmap.md").exists()
