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

    def test_mentions_pre_1_0_note(self):
        # GOV-CLAUDE-MD-1.0-RESYNC-001 : la trajectoire publique est 1.0
        # (bêta en cours). La convention « pas d'aliases avant le tag
        # stable » se rattache désormais au tag 1.0.0.
        content = self.content.lower()
        assert "pré-1.0" in content or "pre-1.0" in content, (
            "CLAUDE.md devrait mentionner la note pré-1.0 (pas d'aliases "
            "avant le tag 1.0.0 stable)"
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


# ── Règle : pas de validations Forge en arrière-plan ──────────────────────────


# Caractères Unicode présents tels quels dans CLAUDE.md (smart quotes).
# RIGHT SINGLE QUOTATION MARK (U+2019) — `’`
# LEFT/RIGHT DOUBLE QUOTATION MARK (U+201C / U+201D) — `“ ”`
_RULE_HEADER = "### Validations : pas d’attente passive"
_J_ATTENDS = "“j’attends la fin”"


def _validation_rule_block() -> str:
    """Extrait le bloc « Validations : pas d'attente passive » de
    CLAUDE.md (du header jusqu'à la prochaine section `##`/`###` ou
    EOF) pour pouvoir vérifier que les marqueurs requis sont DANS la
    règle elle-même, pas ailleurs dans le fichier."""
    text = CLAUDE_MD.read_text(encoding="utf-8")
    start = text.find(_RULE_HEADER)
    if start == -1:
        return ""
    # Trouve la fin du bloc : prochain `##` (header de section) après
    # le header de notre sous-section.
    rest = text[start + len(_RULE_HEADER):]
    next_section_offset = rest.find("\n## ")
    if next_section_offset == -1:
        return text[start:]
    return text[start: start + len(_RULE_HEADER) + next_section_offset]


class TestNoBackgroundValidationRule:
    """Verrouille AGENTS-NO-BACKGROUND-VALIDATION-001 :
    CLAUDE.md doit interdire explicitement les validations Forge en
    arrière-plan, l'attente passive et le masquage par tail/head.
    """

    @pytest.fixture(autouse=True)
    def _load(self):
        self.content = CLAUDE_MD.read_text(encoding="utf-8")
        self.block = _validation_rule_block()

    def test_rule_header_present(self):
        assert _RULE_HEADER in self.content, (
            "CLAUDE.md doit comporter la sous-section "
            "« Validations : pas d’attente passive » "
            "(AGENTS-NO-BACKGROUND-VALIDATION-001)."
        )

    def test_rule_block_extractable(self):
        # Garde-fou de l'extracteur : la règle a bien un corps non vide
        assert self.block, "Bloc de règle introuvable"
        assert len(self.block) > 200, (
            "Le bloc de règle semble tronqué — vérifier que les listes "
            "Interdit/Attendu sont bien présentes."
        )

    @pytest.mark.parametrize("marker", [
        # Concepts-clés (présents dans la règle elle-même)
        "arrière-plan",
        "foreground",
        "exit code",
        # Outils ciblés par l'interdiction
        "pytest",
        "mkdocs",
        "ruff",
        "compileall",
        # Anti-patterns nommés
        "tail",
        "head",
        # Réponse-type interdite, citée littéralement avec smart quotes
        _J_ATTENDS,
    ])
    def test_marker_present_in_rule_block(self, marker: str):
        assert marker in self.block, (
            f"Le marqueur '{marker}' doit apparaître DANS la sous-section "
            "« Validations : pas d’attente passive » de CLAUDE.md "
            "(et pas seulement ailleurs dans le fichier)."
        )

    def test_rule_lists_interdit_and_attendu(self):
        # Les deux listes structurantes (Interdit / Attendu) sont
        # exigées : le contraste rend la règle non ambiguë.
        assert "Interdit :" in self.block, (
            "Le bloc doit comporter une liste « Interdit : »."
        )
        assert "Attendu :" in self.block, (
            "Le bloc doit comporter une liste « Attendu : »."
        )

    def test_rule_is_inside_hooks_section(self):
        # La règle doit cohabiter avec les autres consignes agent —
        # placée dans la section 12 (Fichiers protégés — hook
        # PreToolUse), pas perdue ailleurs dans le fichier.
        text = self.content
        idx_section_12 = text.find("## 12. Fichiers prot")
        idx_rule = text.find(_RULE_HEADER)
        assert idx_section_12 != -1, (
            "Section 12 « Fichiers protégés — hook PreToolUse » "
            "introuvable dans CLAUDE.md."
        )
        assert idx_rule != -1, "Sous-section de règle introuvable."
        assert idx_rule > idx_section_12, (
            "La règle « Validations : pas d’attente passive » doit "
            "être à l'intérieur de la section 12 (hooks/agents), pas "
            "avant — sinon elle est isolée des autres consignes agent."
        )
