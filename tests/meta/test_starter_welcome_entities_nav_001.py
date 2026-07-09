"""Tests documentaires — STARTER-WELCOME-ENTITIES-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-entities`
(moteur d'entités `forge-mvc-entities`, ADR-070, 3 niveaux) : chaînage des
paliers, bascule de niveau par les bilans, et absence de commande de création
(`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
WELCOME = PROJECT_ROOT / "packages" / "forge-mvc-entities" / "docs" / "welcome"

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


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/entity-welcome.md", "(entity-make.md)")
        assert _has("debutant/entity-make.md", "(relation-make.md)")
        assert _has("debutant/relation-make.md", "(build-model.md)")
        assert _has("debutant/build-model.md", "(crud-make.md)")
        assert _has("debutant/crud-make.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/migrations.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/migrations.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/pivot-welcome.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/pivot-welcome.md", "(pivot-make.md)")
        assert _has("avance/pivot-make.md", "(pivot-schema.md)")
        assert _has("avance/pivot-schema.md", "(pivot-attach.md)")
        assert _has("avance/pivot-attach.md", "(pivot-update.md)")
        assert _has("avance/pivot-update.md", "(pivot-list.md)")
        assert _has("avance/pivot-list.md", "(pivot-constraints.md)")
        assert _has("avance/pivot-constraints.md", "(pivot-unique.md)")
        assert _has("avance/pivot-unique.md", "(pivot-form.md)")
        assert _has("avance/pivot-form.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestInstallationPointsToFirstPalier:

    def test_installation_links_first_debutant(self):
        assert _has("installation.md", "debutant/entity-welcome.md")


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
