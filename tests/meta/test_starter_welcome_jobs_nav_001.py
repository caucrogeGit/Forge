"""Tests documentaires — STARTER-WELCOME-JOBS-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-jobs` (module
opt-in `forge-mvc-jobs`, 3 niveaux) : chaînage, bilans, et absence de commande de
création de projet (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
WELCOME = PROJECT_ROOT / "packages" / "forge-mvc-jobs" / "docs" / "welcome"

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
            "debutant/jobs-welcome.md",
            "debutant/jobs-handler.md",
            "debutant/bilan.md",
            "intermediaire/jobs-worker.md",
            "intermediaire/jobs-retry.md",
            "intermediaire/bilan.md",
            "avance/jobs-perimeter.md",
            "avance/jobs-independance.md",
            "avance/bilan.md",
        ],
    )
    def test_page_exists(self, page: str) -> None:
        assert (WELCOME / page).is_file(), f"page welcome manquante : {page}"


class TestDebutantChain:
    # Chaîne dérivée du nav pour tous les paquets
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_bilan_points_to_next_level(self) -> None:
        assert _has("debutant/bilan.md", "../intermediaire/jobs-worker.md")


class TestIntermediaireChain:
    # Chaîne dérivée du nav pour tous les paquets
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_bilan_points_to_next_level(self) -> None:
        assert _has("intermediaire/bilan.md", "../avance/jobs-perimeter.md")


class TestAvanceChain:
    # Chaîne dérivée du nav pour tous les paquets
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_bilan_closes_parcours(self) -> None:
        assert _has("avance/bilan.md", "../../references/queue.md")


class TestNoProjectCreationCommand:
    @pytest.mark.parametrize("page", _pages(), ids=lambda p: p.name)
    def test_no_forbidden_command(self, page: Path) -> None:
        text = page.read_text(encoding="utf-8")
        offending = [cmd for cmd in FORBIDDEN_COMMANDS if cmd in text]
        assert not offending, f"{page.name} contient une commande interdite : {offending}"
