"""Tests documentaires — STARTER-WELCOME-AUDIO-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-audio`
(module opt-in `forge-mvc-audio`, sans état, 2 niveaux thématiques) :

- chaque palier pointe vers le suivant ;
- le dernier palier d'un niveau pointe vers le bilan du niveau ;
- le bilan débutant renvoie au premier palier avancé, le bilan avancé au
  récapitulatif ;
- aucune commande de création dans les pages de palier (`installation.md`
  exempté).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
AUDIO = PROJECT_ROOT / "packages" / "forge-mvc-audio" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    # STARTERS-WELCOME-INSTALL-001 — `installation.md` (préambule) exempté.
    return [p for p in AUDIO.rglob("*.md") if p.name != "installation.md"]


def _has(page: str, needle: str) -> bool:
    return needle in (AUDIO / page).read_text(encoding="utf-8")


class TestDebutantChain:

    def test_chain(self):
        assert _has("debutant/audio-welcome.md", "(audio-upload.md)")
        assert _has("debutant/audio-upload.md", "(audio-play.md)")
        assert _has("debutant/audio-play.md", "(bilan.md)")

    def test_bilan_points_to_next_level(self):
        assert _has("debutant/bilan.md", "../avance/audio-probe.md")


class TestAvanceChain:

    def test_chain(self):
        assert _has("avance/audio-probe.md", "(audio-transcode.md)")
        assert _has("avance/audio-transcode.md", "(audio-doctor.md)")
        assert _has("avance/audio-doctor.md", "(bilan.md)")

    def test_bilan_points_to_recapitulatif(self):
        assert _has("avance/bilan.md", "../recapitulatif.md")


class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page}."
            )
