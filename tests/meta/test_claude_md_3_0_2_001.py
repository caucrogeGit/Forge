"""Garde-fou GOV-CLAUDE-MD-1.0-RESYNC-001 (ex CLAUDE-MD-3.0.2-REFRESH-001).

Historique : ce fichier verrouillait autrefois le récit « Forge 3.0.2 /
série 3.x » dans CLAUDE.md. La trajectoire publique a depuis été
renumérotée vers **1.0** (bêta en cours, ``1.0.0-beta.x``) : le briefing
ne doit plus se présenter comme une version 3.0.x, sinon il ment sur la
réalité du dépôt (``pyproject.toml`` fait foi — section 8 de CLAUDE.md).

Ce garde-fou empêche désormais la réapparition du récit 3.0.x et vérifie
que CLAUDE.md reflète la trajectoire 1.0, tout en préservant la
structure du document (charte v2, règle A « retirer la cause » et règle
D « les tests testent le code, pas la documentation »).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
CLAUDE_MD = PROJECT_ROOT / "CLAUDE.md"


def _text() -> str:
    return CLAUDE_MD.read_text(encoding="utf-8")


class TestNoStaleVersionNarrative:
    """CLAUDE.md ne doit plus se présenter comme une version 3.0.x."""

    @pytest.mark.parametrize("fragment", [
        "refondu pour **Forge 3.0.2**",
        "consolidation 3.0.2 en cours",
        "Série 3.x stable",
        "pendant toute la série 3.x",
        "refondu pour **Forge 2.10.0**",
        "Refonte vers 3.0 en cours",
    ])
    def test_no_obsolete_version_claim(self, fragment):
        assert fragment not in _text(), (
            f"CLAUDE.md contient encore une mention de version périmée : "
            f"{fragment!r}. La trajectoire publique est 1.0 (bêta)."
        )


class TestReflectsOneZeroTrajectory:
    """CLAUDE.md doit refléter la trajectoire publique 1.0."""

    def test_mentions_1_0_beta(self):
        text = _text()
        assert "1.0.0-beta" in text or "bêta publique 1.0" in text, (
            "CLAUDE.md doit indiquer la trajectoire publique 1.0 "
            "(bêta, 1.0.0-beta.x)."
        )

    def test_mentions_serie_1_x(self):
        assert "série 1.x" in _text(), (
            "CLAUDE.md doit mentionner 'la série 1.x' pour clarifier la "
            "période de validité du briefing."
        )

    def test_pre_1_0_note_present(self):
        text = _text().lower()
        assert "pré-1.0" in text, (
            "CLAUDE.md doit porter la note pré-1.0 (pas d'aliases avant le "
            "tag 1.0.0 stable)."
        )


class TestModulesAndAdrCurrent:
    """Le briefing liste les 6 modules et les ADR existants."""

    @pytest.mark.parametrize("module", [
        "forge-mvc-mfa",
        "forge-mvc-rbac",
        "forge-mvc-workflow",
        "forge-mvc-stats",
        "forge-mvc-media",
        "forge-mvc-iot",
    ])
    def test_module_listed(self, module):
        assert module in _text(), (
            f"CLAUDE.md doit lister le module officiel {module}."
        )

    @pytest.mark.parametrize("adr", [
        "ADR-009", "ADR-010", "ADR-011",
        "ADR-012", "ADR-013", "ADR-014", "ADR-015",
    ])
    def test_adr_listed(self, adr):
        assert adr in _text(), (
            f"CLAUDE.md (tableau §4) doit lister {adr}."
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
        assert section in _text(), (
            f"Section '{section}' manquante. Refactor trop agressif ?"
        )

    def test_charte_v2_11_principes_mentioned(self):
        assert "11 principes" in _text(), (
            "La charte v2 a 11 principes — la mention doit rester."
        )
