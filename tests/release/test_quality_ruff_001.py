"""Tests pour QUALITY-RUFF-001 — Intégration de ruff comme linter officiel."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def test_ruff_dans_requirements_dev():
    """requirements-dev.txt mentionne ruff."""
    content = (ROOT / "requirements-dev.txt").read_text(encoding="utf-8")
    assert "ruff" in content


def test_pyproject_contient_section_tool_ruff():
    """pyproject.toml contient [tool.ruff]."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.ruff]" in content


def test_pyproject_ruff_lint_select_e_f():
    """pyproject.toml configure ruff avec les règles E et F."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "[tool.ruff.lint]" in content
    assert '"E"' in content or "'E'" in content
    assert '"F"' in content or "'F'" in content


def test_pyproject_ruff_line_length():
    """pyproject.toml définit line-length pour ruff."""
    content = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    assert "line-length" in content


def test_release_md_mentionne_ruff_check():
    """docs/release/release.md mentionne ruff check dans la checklist."""
    content = (ROOT / "docs" / "release" / "release.md").read_text(encoding="utf-8")
    assert "ruff check" in content


def test_ci_workflow_mentionne_ruff():
    """Le workflow CI tests.yml mentionne ruff."""
    content = (ROOT / ".github" / "workflows" / "tests.yml").read_text(encoding="utf-8")
    assert "ruff" in content


def test_roadmap_reference_quality_ruff_001():
    """forge-roadmap.md référence QUALITY-RUFF-001."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "QUALITY-RUFF-001" in content


def test_roadmap_reference_session_file_store():
    """forge-roadmap.md mentionne SESSION-FILE-STORE-001 comme prochaine priorité."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "SESSION-FILE-STORE-001" in content
