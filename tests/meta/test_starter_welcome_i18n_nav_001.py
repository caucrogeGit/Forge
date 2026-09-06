"""Tests documentaires — STARTER-WELCOME-I18N-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-i18n`
(module opt-in `forge-mvc-i18n`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
I18N = PROJECT_ROOT / "packages" / "forge-mvc-i18n" / "docs" / "welcome"

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

    # La chaîne page par page vivait ici, et figeait la liste d'alors plutôt
    # que la propriété. Elle est dérivée du `nav` pour tous les paquets par
    # `tests/meta/test_welcome_chaines_derivees_001.py`
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/i18n-locale.md")


class TestIntermediaireChain:

    # La chaîne page par page vivait ici, et figeait la liste d'alors plutôt
    # que la propriété. Elle est dérivée du `nav` pour tous les paquets par
    # `tests/meta/test_welcome_chaines_derivees_001.py`
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/i18n-jinja.md")


class TestAvanceChain:

    # La chaîne page par page vivait ici, et figeait la liste d'alors plutôt
    # que la propriété. Elle est dérivée du `nav` pour tous les paquets par
    # `tests/meta/test_welcome_chaines_derivees_001.py`
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")



class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
