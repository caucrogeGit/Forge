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

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
VIDEO = PROJECT_ROOT / "packages" / "forge-mvc-video" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    # STARTERS-WELCOME-INSTALL-001 — `installation.md` est le préambule
    # d'installation, seule page du parcours autorisée à porter les commandes
    # de création/build (elle crée justement le projet). Exemptée de l'hygiène
    # « pas de commande de création » ci-dessous.
    return [p for p in VIDEO.rglob("*.md") if p.name != "installation.md"]


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

    def test_video_upload_points_to_video_playback(self):
        page = VIDEO / "intermediaire" / "video-upload.md"
        assert "(video-playback.md)" in page.read_text(encoding="utf-8")

    def test_video_playback_points_to_video_status(self):
        page = VIDEO / "intermediaire" / "video-playback.md"
        assert "(video-status.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # video-status est (pour l'instant) le dernier palier intermédiaire.
        page = VIDEO / "intermediaire" / "video-status.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_intermediaire_bilan_points_to_next_level(self):
        # Le niveau avancé existe → le bilan intermédiaire renvoie à son
        # premier palier.
        bilan = VIDEO / "intermediaire" / "bilan.md"
        assert "../avance/video-probe.md" in bilan.read_text(encoding="utf-8")


# ── Niveau avancé ─────────────────────────────────────────────────────────────

class TestAvanceChain:

    def test_video_probe_points_to_video_transcode(self):
        page = VIDEO / "avance" / "video-probe.md"
        assert "(video-transcode.md)" in page.read_text(encoding="utf-8")

    def test_video_transcode_points_to_video_doctor(self):
        page = VIDEO / "avance" / "video-transcode.md"
        assert "(video-doctor.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # video-doctor est le dernier palier avancé (et de toute la progression).
        page = VIDEO / "avance" / "video-doctor.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_avance_bilan_points_to_recapitulatif(self):
        # Dernier niveau → le bilan avancé renvoie au récapitulatif.
        bilan = VIDEO / "avance" / "bilan.md"
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
