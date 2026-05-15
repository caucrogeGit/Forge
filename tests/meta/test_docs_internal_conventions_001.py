"""Tests DOCS-INTERNAL-CONVENTIONS-001 : conventions opérationnelles de Forge."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONVENTIONS = PROJECT_ROOT / "docs" / "contributing" / "conventions.md"


class TestFileExists:
    def test_conventions_file_exists(self):
        assert CONVENTIONS.exists(), (
            "docs/contributing/conventions.md doit exister "
            "(DOCS-INTERNAL-CONVENTIONS-001)"
        )


class TestStructure:
    def setup_method(self):
        self.content = CONVENTIONS.read_text(encoding="utf-8")

    @pytest.mark.parametrize("section_title", [
        "A. Audit avant action",
        "B. Tests",
        "C. Code",
        "D. Documentation",
    ])
    def test_section_present(self, section_title):
        assert section_title in self.content, (
            f"La section '{section_title}' doit être présente dans le document"
        )


class TestPatternsDocumented:
    """Au moins les 18 patterns sont documentés (via des mots-clés repères)."""

    def setup_method(self):
        self.content = CONVENTIONS.read_text(encoding="utf-8")

    @pytest.mark.parametrize("pattern_keyword", [
        # A
        "Audit 5 racines",
        "gitignore",
        "historique git",
        "production interne",
        "documentation référencée",
        # B
        "Helper local",
        "module.__file__",
        "PROJECT_ROOT",
        "Classification sémantique",
        "Généraliser plutôt",
        "noms de fonctions de tests",
        # C
        "lock + delegate",
        "register_",
        "Module extrait",
        "garde-fous",
        "word boundaries",
        # D
        "MkDocs strict",
        "history/",
        "Historique",
    ])
    def test_pattern_mentioned(self, pattern_keyword):
        assert pattern_keyword in self.content, (
            f"Le pattern '{pattern_keyword}' doit être mentionné dans "
            f"docs/contributing/conventions.md"
        )


class TestPointsToCanonicalSources:
    """Le document pointe vers les sources canoniques connexes."""

    def setup_method(self):
        self.content = CONVENTIONS.read_text(encoding="utf-8")

    @pytest.mark.parametrize("reference", [
        "CHARTE_DOC.md",
        "docs/adr/",
        "CLAUDE.md",
        "CHANGELOG.md",
    ])
    def test_references_canonical_source(self, reference):
        assert reference in self.content, (
            f"Le document devrait référencer '{reference}'"
        )


class TestClaudeMdPointsToConventions:
    """CLAUDE.md section 9 pointe vers le nouveau fichier conventions.md."""

    def test_claude_md_references_conventions(self):
        claude_md = (PROJECT_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
        assert "contributing/conventions.md" in claude_md, (
            "CLAUDE.md devrait pointer vers docs/contributing/conventions.md"
        )
