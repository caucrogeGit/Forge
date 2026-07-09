"""Tests documentaires — STARTER-WELCOME-SETTINGS-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-settings`
(module opt-in `forge-mvc-settings`, 3 niveaux) : chaînage, bilans, et absence
de commande de création de projet (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
WELCOME = PROJECT_ROOT / "packages" / "forge-mvc-settings" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in WELCOME.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (WELCOME / page).read_text(encoding="utf-8")


class TestPagesExist:
    @pytest.mark.parametrize(
        "page",
        [
            "recapitulatif.md",
            "debutant/settings-welcome.md",
            "debutant/settings-set-get.md",
            "debutant/bilan.md",
            "intermediaire/settings-types.md",
            "intermediaire/settings-all.md",
            "intermediaire/bilan.md",
            "avance/settings-keys.md",
            "avance/settings-independance.md",
            "avance/bilan.md",
        ],
    )
    def test_page_exists(self, page: str) -> None:
        assert (WELCOME / page).is_file(), f"page welcome manquante : {page}"


class TestDebutantChain:
    def test_chain(self) -> None:
        assert _has("debutant/settings-welcome.md", "(settings-set-get.md)")
        assert _has("debutant/settings-set-get.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self) -> None:
        assert _has("debutant/bilan.md", "../intermediaire/settings-types.md")


class TestIntermediaireChain:
    def test_chain(self) -> None:
        assert _has("intermediaire/settings-types.md", "(settings-all.md)")
        assert _has("intermediaire/settings-all.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self) -> None:
        assert _has("intermediaire/bilan.md", "../avance/settings-keys.md")


class TestAvanceChain:
    def test_chain(self) -> None:
        assert _has("avance/settings-keys.md", "(settings-independance.md)")
        assert _has("avance/settings-independance.md", "(bilan.md)")

    def test_bilan_closes_parcours(self) -> None:
        assert _has("avance/bilan.md", "../../references/store.md")


class TestNoProjectCreationCommand:
    @pytest.mark.parametrize("page", _pages(), ids=lambda p: p.name)
    def test_no_forbidden_command(self, page: Path) -> None:
        text = page.read_text(encoding="utf-8")
        offending = [cmd for cmd in FORBIDDEN_COMMANDS if cmd in text]
        assert not offending, f"{page.name} contient une commande interdite : {offending}"
