"""Tests documentaires — STARTER-WELCOME-FILES-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-files`
(module opt-in `forge-mvc-files`), calquée sur welcome-images :

- chaque palier pointe vers le suivant ;
- le dernier palier d'un niveau pointe vers le bilan du niveau ;
- chaque bilan renvoie au premier palier du niveau suivant, le dernier au
  récapitulatif ;
- aucune commande de création dans les pages de palier (`installation.md`,
  le préambule, en est la seule exception).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
FILES = PROJECT_ROOT / "docs" / "starters" / "welcome-files"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    # STARTERS-WELCOME-INSTALL-001 — `installation.md` (préambule) est la seule
    # page autorisée à porter les commandes de création. Exemptée ci-dessous.
    return [p for p in FILES.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (FILES / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/files-welcome.md", "(file-store.md)")
        assert _has("debutant/file-store.md", "(file-serve.md)")
        assert _has("debutant/file-serve.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../intermediaire/file-validate.md")


class TestIntermediaireChain:

    def test_chain(self):
        assert _has("intermediaire/file-validate.md", "(file-rate-limit.md)")
        assert _has("intermediaire/file-rate-limit.md", "(file-delete.md)")
        assert _has("intermediaire/file-delete.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("intermediaire/bilan.md", "../avance/file-safe-name.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/file-safe-name.md", "(file-safe-path.md)")
        assert _has("avance/file-safe-path.md", "(file-bytes.md)")
        assert _has("avance/file-bytes.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
