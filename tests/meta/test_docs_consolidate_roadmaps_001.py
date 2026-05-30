"""Tests DOCS-CONSOLIDATE-ROADMAPS-001 : consolidation des roadmaps Forge.

Verifie que :
- les 3 fichiers archives sont dans docs/history/ et non dans docs/roadmap/ ;
- forge-roadmap.md contient la section Phase 14 ;
- mkdocs.yml ne liste plus les archives dans la section Roadmap ;
- CLAUDE.md pointe vers forge-roadmap.md et non vers forge-roadmap-post-2.0.md ;
- contributing.md ne reference plus forge_post_2_0_consolidation_roadmap.md.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]


# ── Fichiers archives deplaces vers docs/history/ ─────────────────────────────

_ARCHIVED_FILES = [
    "forge_post_2_0_consolidation_roadmap.md",
    "forge-roadmap-post-2.0.md",
    "forge-roadmap-ux.md",
]


@pytest.mark.parametrize("filename", _ARCHIVED_FILES)
class TestArchivedFilesInHistory:

    def test_file_in_history(self, filename):
        assert (ROOT / "docs" / "history" / filename).exists(), (
            f"{filename} devrait etre dans docs/history/"
        )

    def test_file_not_in_roadmap(self, filename):
        assert not (ROOT / "docs" / "roadmap" / filename).exists(), (
            f"{filename} ne devrait plus etre dans docs/roadmap/"
        )


# ── forge-roadmap.md enrichi avec Phase 14 ───────────────────────────────────

class TestForgeRoadmapContainsPhase14:

    @pytest.fixture(scope="class")
    def roadmap_content(self):
        return (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")

    def test_phase_14_section_exists(self, roadmap_content):
        assert "Phase 14" in roadmap_content

    def test_phase_14_1_subsection(self, roadmap_content):
        assert "14.1" in roadmap_content

    def test_phase_14_2_subsection(self, roadmap_content):
        assert "14.2" in roadmap_content

    def test_phase_14_3_subsection(self, roadmap_content):
        assert "14.3" in roadmap_content

    def test_phase_14_4_subsection(self, roadmap_content):
        assert "14.4" in roadmap_content

    def test_forge_3_mentioned(self, roadmap_content):
        assert "3.0" in roadmap_content

    def test_extraction_mfa_mentioned(self, roadmap_content):
        assert "MFA-EXTRACT-001" in roadmap_content

    def test_lang_migration_mentioned(self, roadmap_content):
        assert "LANG-MIGRATION-001" in roadmap_content

    def test_this_ticket_mentioned(self, roadmap_content):
        assert "DOCS-CONSOLIDATE-ROADMAPS-001" in roadmap_content


# ── mkdocs.yml coherent ───────────────────────────────────────────────────────

class TestMkdocsYmlCoherent:

    @pytest.fixture(scope="class")
    def mkdocs_content(self):
        return (ROOT / "mkdocs.yml").read_text(encoding="utf-8")

    def test_archived_consolidation_roadmap_not_in_roadmap_nav(self, mkdocs_content):
        lines = mkdocs_content.splitlines()
        in_roadmap_section = False
        for line in lines:
            stripped = line.strip()
            if "- Roadmap:" in stripped:
                in_roadmap_section = True
            elif in_roadmap_section and "- Historique:" in stripped:
                in_roadmap_section = False
            elif in_roadmap_section and "forge_post_2_0_consolidation_roadmap" in stripped:
                pytest.fail(
                    "forge_post_2_0_consolidation_roadmap.md trouve dans la section Roadmap"
                )

    def test_archived_files_referenced_in_history(self, mkdocs_content):
        assert "history/forge_post_2_0_consolidation_roadmap.md" in mkdocs_content

    def test_forge_roadmap_still_in_nav(self, mkdocs_content):
        assert "roadmap/forge-roadmap.md" in mkdocs_content

    def test_forge_design_still_in_nav(self, mkdocs_content):
        assert "roadmap/forge-design-roadmap.md" in mkdocs_content


# ── CLAUDE.md pointe vers forge-roadmap.md ────────────────────────────────────

class TestClaudeMdPointsToCorrectRoadmap:

    @pytest.fixture(scope="class")
    def claude_content(self):
        return (ROOT / "CLAUDE.md").read_text(encoding="utf-8")

    def test_does_not_reference_post_2_0_roadmap(self, claude_content):
        assert "forge-roadmap-post-2.0.md" not in claude_content

    def test_references_forge_roadmap(self, claude_content):
        assert "forge-roadmap.md" in claude_content


# ── contributing.md ne reference plus le fichier archive ─────────────────────

class TestContributingMdUpdated:

    @pytest.fixture(scope="class")
    def contributing_content(self):
        return (ROOT / "docs" / "philosophy" / "contributing.md").read_text(encoding="utf-8")

    def test_no_reference_to_archived_consolidation_roadmap(self, contributing_content):
        assert "forge_post_2_0_consolidation_roadmap" not in contributing_content
