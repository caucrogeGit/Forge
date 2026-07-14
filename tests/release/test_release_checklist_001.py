"""Tests pour RELEASE-CHECKLIST-001 — Procédure de release Forge."""

from __future__ import annotations

from pathlib import Path
import pytest

pytestmark = pytest.mark.docs

ROOT = Path(__file__).resolve().parents[2]


def test_release_md_existe():
    """docs/release/release.md existe."""
    assert (ROOT / "docs" / "release" / "release.md").exists()


def test_release_md_mentionne_pytest():
    """docs/release/release.md documente pytest."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "pytest" in content


def test_release_md_mentionne_mkdocs_strict():
    """docs/release/release.md documente mkdocs build --strict."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "mkdocs build --strict" in content


def test_release_md_mentionne_python_m_build():
    """docs/release/release.md documente python -m build."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "python -m build" in content


def test_release_md_mentionne_git_tag():
    """docs/release/release.md documente la création du tag."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "git tag" in content


def test_release_md_mentionne_git_push():
    """docs/release/release.md documente git push."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "git push" in content


def test_release_md_mentionne_changelog():
    """docs/release/release.md documente CHANGELOG.md."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "CHANGELOG" in content


def test_mkdocs_yml_reference_release_md():
    """mkdocs.yml référence release.md."""
    content = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "release.md" in content


def test_roadmap_reference_release_checklist_001():
    """forge-roadmap.md référence RELEASE-CHECKLIST-001."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(
        encoding="utf-8"
    )
    assert "RELEASE-CHECKLIST-001" in content
