"""Garde-fou WELCOME-PROJET-NAV-001 (ADR-048).

Le parcours d'accueil embarqué dans le squelette (`cli/skeleton/data/docs/welcome/`)
est correctement chaîné : chaque étape lie la suivante, chaque bilan lie le niveau
suivant ou le récapitulatif, et aucune commande de création de projet n'y figure
(le parcours s'exécute dans un projet déjà créé).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent
WELCOME = PROJECT_ROOT / "cli" / "skeleton" / "data" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge new",
    "forge starter:build",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _has(page: str, needle: str) -> bool:
    return needle in (WELCOME / page).read_text(encoding="utf-8")


def test_installation_pointe_premier_palier():
    assert _has("installation.md", "debutant/premiere-entite.md")


class TestDebutantChain:
    def test_chain(self):
        assert _has("debutant/premiere-entite.md", "(premier-crud.md)")
        assert _has("debutant/premier-crud.md", "(bilan.md)")

    def test_bilan_pointe_niveau_suivant(self):
        assert _has("debutant/bilan.md", "../intermediaire/page-publique.md")


class TestIntermediaireChain:
    def test_chain(self):
        assert _has("intermediaire/page-publique.md", "(controleur-template.md)")
        assert _has("intermediaire/controleur-template.md", "(bilan.md)")

    def test_bilan_pointe_niveau_suivant(self):
        assert _has("intermediaire/bilan.md", "../avance/un-optin.md")


class TestAvanceChain:
    def test_chain(self):
        assert _has("avance/un-optin.md", "(valider-livrer.md)")
        assert _has("avance/valider-livrer.md", "(bilan.md)")

    def test_bilan_pointe_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestForbiddenCommandsAbsent:
    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in WELCOME.rglob("*.md"):
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page.relative_to(WELCOME)}."
            )
