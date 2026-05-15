"""Tests CLAUDE-MD-UPDATE-001 : le briefing IA est coherent et mentionne
les elements structurants.

Verifie que CLAUDE.md :
- existe
- mentionne les concepts cles stables (charte, ADR, core minimal, Python 3.12, CHANGELOG)
- ne contient pas d'informations volatiles (compteur de tests precis)
- pointe vers les sources canoniques (pyproject.toml, CHANGELOG.md, docs/adr)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

CLAUDE_MD = Path("CLAUDE.md")


# ── Existence ──────────────────────────────────────────────────────────────────

class TestFileExists:

    def test_claude_md_exists(self):
        assert CLAUDE_MD.exists(), "CLAUDE.md doit exister"

    def test_claude_md_not_empty(self):
        assert len(CLAUDE_MD.read_text(encoding="utf-8")) > 500, (
            "CLAUDE.md semble vide ou trop court pour être utile"
        )


# ── Elements structurants ──────────────────────────────────────────────────────

class TestStructuralElements:
    """Le briefing mentionne les concepts cles stables.
    Si ces elements disparaissent, le briefing perd sa valeur pour un agent IA."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CLAUDE_MD.read_text(encoding="utf-8")

    @pytest.mark.parametrize("keyword", [
        "charte",       # reference a la charte v2
        "ADR",          # reference aux ADR
        "core minimal", # principe d'architecture
        "Python 3.12",  # version minimum
        "CHANGELOG",    # source canonique pour l'historique
        "pyproject.toml",  # source canonique pour la version
        "CHARTE_DOC",   # chemin vers la charte complete
    ])
    def test_mentions_structural_keyword(self, keyword):
        assert keyword.lower() in self.content.lower(), (
            f"CLAUDE.md devrait mentionner '{keyword}' (concept structurant)"
        )

    def test_mentions_all_11_principles(self):
        content = self.content.lower()
        assert "11 principes" in content or "11. " in self.content, (
            "CLAUDE.md devrait mentionner les 11 principes de la charte v2"
        )

    def test_mentions_pre_3_note(self):
        content = self.content.lower()
        assert "pré-3.0" in content or "pre-3" in content or "avant.*3.0" in content.replace("\n", " "), (
            "CLAUDE.md devrait mentionner la note pré-3.0 (pas d'aliases avant le tag 3.0)"
        )

    def test_mentions_adr_list(self):
        assert "ADR-003" in self.content and "ADR-007" in self.content, (
            "CLAUDE.md devrait lister les ADR existants"
        )


# ── Pas d'informations volatiles ───────────────────────────────────────────────

class TestNoVolatileInformation:
    """Le briefing ne contient pas d'informations qui deviendraient obsoletes
    a chaque ticket."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CLAUDE_MD.read_text(encoding="utf-8")

    def test_no_precise_test_count(self):
        """Pas de mention de 'N tests passants' avec un nombre precis."""
        matches = re.findall(r"\b\d{3,5}\s+tests?\b", self.content)
        assert not matches, (
            f"CLAUDE.md contient des compteurs de tests precis (volatil) : {matches}. "
            "Utiliser 'python -m pytest' ou pointer vers pytest."
        )

    def test_no_specific_ticket_in_progress(self):
        """Pas de section 'Prochain ticket : X-001' qui serait obsolete."""
        assert "Prochain ticket" not in self.content, (
            "CLAUDE.md ne doit pas mentionner le ticket suivant (volatil). "
            "Pointer vers la roadmap."
        )

    def test_no_specific_phase_progress(self):
        """Pas de 'Phase 4.5 : X' ou 'Phase 14.3' en cours."""
        assert "Phase 4.5" not in self.content, (
            "CLAUDE.md contient une reference a Phase 4.5 (obsolete depuis 2.x)"
        )


# ── Pointeurs vers sources canoniques ─────────────────────────────────────────

class TestPointsToSources:
    """Le briefing pointe vers les sources canoniques pour les infos volatiles."""

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CLAUDE_MD.read_text(encoding="utf-8")

    @pytest.mark.parametrize("source", [
        "pyproject.toml",
        "CHANGELOG.md",
        "docs/adr",
        "docs/roadmap",
    ])
    def test_mentions_canonical_source(self, source):
        assert source in self.content, (
            f"CLAUDE.md devrait pointer vers la source canonique '{source}'"
        )
