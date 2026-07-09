"""Tests documentaires — STARTER-WELCOME-ADMIN-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-admin`
(module opt-in `forge-mvc-admin`, 3 niveaux) : chaînage, bilans, et absence de
commande de création (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


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


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/admin-welcome.md", "(admin-resource.md)")
        assert _has("debutant/admin-resource.md", "(admin-list.md)")
        assert _has("debutant/admin-list.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/admin-detail.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/admin-detail.md", "(admin-new.md)")
        assert _has("intermediaire/admin-new.md", "(admin-edit.md)")
        assert _has("intermediaire/admin-edit.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/admin-delete.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/admin-delete.md", "(admin-override.md)")
        assert _has("avance/admin-override.md", "(admin-rbac.md)")
        assert _has("avance/admin-rbac.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")



class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
