"""Tests documentaires — STARTER-WELCOME-RBAC-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-rbac`
(module opt-in `forge-mvc-rbac`, 3 niveaux) : chaînage des paliers, bilans, et
absence de commande de création dans les pages (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
RBAC = PROJECT_ROOT / "packages" / "forge-mvc-rbac" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in RBAC.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (RBAC / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/rbac-welcome.md", "(rbac-permission.md)")
        assert _has("debutant/rbac-permission.md", "(rbac-role.md)")
        assert _has("debutant/rbac-role.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/rbac-check.md")


# La chaîne est dérivée du nav pour tous les paquets à la fois par
# `tests/meta/test_welcome_chaines_derivees_001.py`
# (`WELCOME-CHAINES-DERIVEES-001`) : la dupliquer ici en ferait deux.


class TestBilansEnchaines:

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/rbac-user-role.md")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")

class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
