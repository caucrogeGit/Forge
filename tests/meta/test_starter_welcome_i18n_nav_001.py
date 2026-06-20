"""Tests documentaires — STARTER-WELCOME-I18N-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-i18n`
(module opt-in `forge-mvc-i18n`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
I18N = PROJECT_ROOT / "docs" / "starters" / "welcome-i18n"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in I18N.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (I18N / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/i18n-welcome.md", "(i18n-catalog.md)")
        assert _has("debutant/i18n-catalog.md", "(i18n-trans.md)")
        assert _has("debutant/i18n-trans.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/i18n-locale.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/i18n-locale.md", "(i18n-fallback.md)")
        assert _has("intermediaire/i18n-fallback.md", "(i18n-missing.md)")
        assert _has("intermediaire/i18n-missing.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/i18n-jinja.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/i18n-jinja.md", "(i18n-cache.md)")
        assert _has("avance/i18n-cache.md", "(i18n-errors.md)")
        assert _has("avance/i18n-errors.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestInstallationPointsToFirstPalier:

    def test_installation_links_first_debutant(self):
        assert _has("installation.md", "debutant/i18n-welcome.md")


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
