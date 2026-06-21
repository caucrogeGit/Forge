"""Tests documentaires — STARTER-WELCOME-MFA-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-mfa`
(module opt-in `forge-mvc-mfa`, 3 niveaux) :

- chaque palier pointe vers le suivant ;
- le dernier palier d'un niveau pointe vers le bilan du niveau ;
- chaque bilan renvoie au premier palier du niveau suivant, le dernier au
  récapitulatif ;
- aucune commande de création dans les pages de palier (`installation.md` exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
MFA = PROJECT_ROOT / "packages" / "forge-mvc-mfa" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return [p for p in MFA.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (MFA / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/mfa-welcome.md", "(mfa-secret.md)")
        assert _has("debutant/mfa-secret.md", "(mfa-verify.md)")
        assert _has("debutant/mfa-verify.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/mfa-enroll.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/mfa-enroll.md", "(mfa-challenge.md)")
        assert _has("intermediaire/mfa-challenge.md", "(mfa-recovery.md)")
        assert _has("intermediaire/mfa-recovery.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/mfa-revalidation.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/mfa-revalidation.md", "(mfa-replay.md)")
        assert _has("avance/mfa-replay.md", "(mfa-crypto.md)")
        assert _has("avance/mfa-crypto.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
