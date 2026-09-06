"""Tests documentaires — STARTER-WELCOME-ADMIN-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-admin`
(module opt-in `forge-mvc-admin`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
ADMIN = PROJECT_ROOT / "packages" / "forge-mvc-admin" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in ADMIN.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (ADMIN / page).read_text(encoding="utf-8")


# La chaîne est dérivée du nav pour tous les paquets à la fois par
# `tests/meta/test_welcome_chaines_derivees_001.py`
# (`WELCOME-CHAINES-DERIVEES-001`) : la dupliquer ici en ferait deux.


class TestBilans:

    def test_debutant_mene_au_niveau_suivant(self):
        assert _has("debutant/bilan.md", "../intermediaire/admin-detail.md")

    def test_intermediaire_mene_au_niveau_suivant(self):
        assert _has("intermediaire/bilan.md", "../avance/admin-delete.md")

    def test_avance_mene_au_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")



class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
