"""Tests documentaires — STARTER-WELCOME-QRCODE-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-qrcode`
(module opt-in `forge-mvc-qrcode`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
QRCODE = PROJECT_ROOT / "packages" / "forge-mvc-qrcode" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in QRCODE.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (QRCODE / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/qrcode-welcome.md", "(qrcode-png.md)")
        assert _has("debutant/qrcode-png.md", "(qrcode-svg.md)")
        assert _has("debutant/qrcode-svg.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/qrcode-controller.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/qrcode-controller.md", "(qrcode-svg-response.md)")
        assert _has("intermediaire/qrcode-svg-response.md", "(qrcode-mime.md)")
        assert _has("intermediaire/qrcode-mime.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/qrcode-errors.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/qrcode-errors.md", "(qrcode-options.md)")
        assert _has("avance/qrcode-options.md", "(qrcode-independance.md)")
        assert _has("avance/qrcode-independance.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")



class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
