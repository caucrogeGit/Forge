"""Tests documentaires — STARTER-WELCOME-VIDEO-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-video`
(module opt-in `forge-mvc-video`), calquée sur le modèle `welcome-forge` :

- chaque palier pointe vers le suivant (fichier frère dans le dossier de
  niveau) ;
- le dernier palier d'un niveau pointe vers le **bilan du niveau** ;
- le bilan renvoie au premier palier du niveau suivant s'il existe, sinon
  au `recapitulatif.md` à la racine du starter ;
- aucune commande de création/installation interdite dans les pages.

Ces assertions grandissent au fil des paliers livrés.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
VIDEO = PROJECT_ROOT / "docs" / "starters" / "welcome-video"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return list(VIDEO.rglob("*.md"))


# ── Niveau débutant ───────────────────────────────────────────────────────────

class TestDebutantChain:

    def test_video_welcome_points_to_video_list(self):
        page = VIDEO / "debutant" / "video-welcome.md"
        assert "(video-list.md)" in page.read_text(encoding="utf-8")

    def test_video_list_points_to_video_detail(self):
        page = VIDEO / "debutant" / "video-list.md"
        assert "(video-detail.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # video-detail est (pour l'instant) le dernier palier débutant.
        page = VIDEO / "debutant" / "video-detail.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_debutant_bilan_points_to_next_level(self):
        # Le niveau intermédiaire existe → le bilan débutant renvoie à son
        # premier palier.
        bilan = VIDEO / "debutant" / "bilan.md"
        assert "../intermediaire/video-upload.md" in bilan.read_text(encoding="utf-8")


# ── Niveau intermédiaire ──────────────────────────────────────────────────────

class TestIntermediaireChain:

    def test_last_palier_points_to_level_bilan(self):
        # video-upload est (pour l'instant) le dernier palier intermédiaire.
        page = VIDEO / "intermediaire" / "video-upload.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_intermediaire_bilan_points_to_recapitulatif(self):
        # Pas encore de niveau avancé → le bilan intermédiaire renvoie au
        # récapitulatif à la racine du starter.
        bilan = VIDEO / "intermediaire" / "bilan.md"
        assert "../recapitulatif.md" in bilan.read_text(encoding="utf-8")


# ── Hygiène des pages ─────────────────────────────────────────────────────────

class TestForbiddenCommandsAbsent:

    @pytest.mark.parametrize("forbidden", FORBIDDEN_COMMANDS)
    def test_command_absent(self, forbidden: str):
        for page in _pages():
            assert forbidden not in page.read_text(encoding="utf-8"), (
                f"`{forbidden}` ne doit pas apparaître dans {page} "
                "(la page suppose un projet déjà créé avec ce starter)."
            )
