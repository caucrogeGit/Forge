"""Tests documentaires — STARTER-WELCOME-OUTILS-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-outils`
(parcours cœur, outils interactifs) : chaînage index → outils → bilan, renvoi au
guide de référence, et absence de commande de création de projet. Vérifie aussi
que les contraintes de sécurité structurantes (CSP 'self', pas de CDN) restent
présentes dans les pages.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
OUTILS = PROJECT_ROOT / "docs" / "starters" / "welcome-outils"
GUIDE = PROJECT_ROOT / "docs" / "features" / "outils-interactifs.md"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _has(page: str, needle: str) -> bool:
    return needle in (OUTILS / page).read_text(encoding="utf-8")


def test_pages_present():
    for name in ("index.md", "subnet-calculator.md", "oscilloscope.md", "bilan.md"):
        assert (OUTILS / name).is_file(), f"{name} manquant dans welcome-outils/"


def test_chain():
    assert _has("index.md", "(subnet-calculator.md)")
    assert _has("subnet-calculator.md", "(oscilloscope.md)")
    assert _has("oscilloscope.md", "(bilan.md)")


def test_bilan_points_to_guide():
    assert _has("bilan.md", "../../features/outils-interactifs.md")


def test_guide_exists_and_links_parcours():
    assert GUIDE.is_file(), "le guide docs/features/outils-interactifs.md doit exister"
    text = GUIDE.read_text(encoding="utf-8")
    assert "../starters/welcome-outils/index.md" in text


def test_security_constraints_present():
    guide = GUIDE.read_text(encoding="utf-8")
    # Le motif JS-live doit rappeler la CSP 'self' et l'interdiction de CDN.
    assert "script-src 'self'" in guide
    assert "CDN" in guide
    osc = (OUTILS / "oscilloscope.md").read_text(encoding="utf-8")
    # L'outil JS-live charge un fichier local, pas un CDN.
    assert "/static/js/oscilloscope.js" in osc


@pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
def test_command_absent(forbidden: str):
    for page in OUTILS.rglob("*.md"):
        assert forbidden not in page.read_text(encoding="utf-8"), (
            f"`{forbidden}` ne doit pas apparaître dans {page}."
        )
