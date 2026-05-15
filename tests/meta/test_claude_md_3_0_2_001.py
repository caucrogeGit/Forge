"""Garde-fou CLAUDE-MD-3.0.2-REFRESH-001.

Vérifie que CLAUDE.md reflète la réalité Forge 3.0.x (et non 2.10.0).

Origine : audit F8 — CLAUDE.md daté de 2.10.0, annonçait 'refonte 3.0 en cours'
alors qu'on est en 3.0.1 stable + 3.0.2 en consolidation.

Conservé intentionnellement :
- Mentions de la refonte 3.0 au passé (patterns émergés pendant...)
- Histoire CLAUDE-MD-UPDATE-001 (ancien ticket créateur du doc)
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


class TestActiveMentionsAreCurrent:

    def test_no_active_2_10_0_refonte(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "refondu pour **Forge 2.10.0**" not in text, (
            "CLAUDE.md mentionne encore 'refondu pour Forge 2.10.0' "
            "comme état courant. Doit être 'Forge 3.0.2'."
        )

    def test_no_active_refonte_3_0_en_cours(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "Refonte vers 3.0 en cours" not in text, (
            "CLAUDE.md disait 'Refonte vers 3.0 en cours'. "
            "Doit être bumpé pour refléter 3.0.2 en consolidation."
        )

    def test_no_active_jusqu_au_tag_3_0_0(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "jusqu'au tag 3.0.0" not in text, (
            "CLAUDE.md promettait 'valide jusqu'au tag 3.0.0'. "
            "Le tag 3.0.0 est posé. Reformuler en 'série 3.x'."
        )

    def test_no_active_prochaine_3_0_0(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "Prochaine mise à jour prévue** : tag 3.0.0" not in text, (
            "CLAUDE.md annonçait 'Prochaine mise à jour : tag 3.0.0'. "
            "Le tag est posé. Annoncer 'tag majeur 4.0' à la place."
        )


class TestAdrTitleMentionsAreCurrent:

    def test_adr_001_title_3_x(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        adr_001_lines = [
            line for line in text.splitlines()
            if "ADR-001" in line and "001-auth-strategy" in line
        ]
        assert adr_001_lines, "Ligne ADR-001 introuvable dans CLAUDE.md"
        for line in adr_001_lines:
            assert "Forge 2.x" not in line, (
                f"Titre ADR-001 contient 'Forge 2.x' : {line!r}. "
                f"Bumper en 'Forge 3.x' (cohérence avec T17)."
            )


class TestNewMentionsAdded:

    def test_mentions_3_0_2(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "3.0.2" in text, (
            "CLAUDE.md doit mentionner la version courante 3.0.2 "
            "(consolidation en cours)."
        )

    def test_mentions_serie_3_x(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "série 3.x" in text or "serie 3.x" in text, (
            "CLAUDE.md doit mentionner 'la série 3.x' pour clarifier "
            "la période de validité du briefing."
        )

    def test_no_obsolete_packaging_note(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "À résoudre par PACKAGING-SRC-LAYOUT-001" not in text, (
            "La note obsolète sur PACKAGING-SRC-LAYOUT-001 (T2/T2b déjà livrés) "
            "doit être retirée ou reformulée."
        )


class TestStructurePreserved:

    @pytest.mark.parametrize("section", [
        "## 1. Identité du projet",
        "## 2. Charte philosophique v2",
        "## 3. Architecture",
        "## 4. ADR",
        "## 5. Convention de tickets",
        "## 6. Convention de tests",
        "## 7. Modes d'action de Forge",
        "## 8. Sources canoniques",
        "## 9. Patterns émergents",
        "## 10. Engagement de mise à jour",
    ])
    def test_main_section_present(self, section):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert section in text, (
            f"Section '{section}' manquante. Refactor trop agressif ?"
        )

    def test_charte_v2_11_principes_mentioned(self):
        text = CLAUDE_MD.read_text(encoding="utf-8")
        assert "11 principes" in text, (
            "La charte v2 a 11 principes — la mention doit rester."
        )
