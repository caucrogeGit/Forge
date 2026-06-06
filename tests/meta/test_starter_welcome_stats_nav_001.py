"""Tests documentaires — STARTER-WELCOME-STATS-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-stats`
(module opt-in `forge-mvc-stats`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
STATS = PROJECT_ROOT / "docs" / "starters" / "welcome-stats"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in STATS.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (STATS / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/stats-welcome.md", "(stats-event.md)")
        assert _has("debutant/stats-event.md", "(stats-schema.md)")
        assert _has("debutant/stats-schema.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/stats-track-sql.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/stats-track-sql.md", "(stats-track.md)")
        assert _has("intermediaire/stats-track.md", "(stats-validate.md)")
        assert _has("intermediaire/stats-validate.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/stats-admin-sql.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/stats-admin-sql.md", "(stats-list.md)")
        assert _has("avance/stats-list.md", "(stats-normalize.md)")
        assert _has("avance/stats-normalize.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
