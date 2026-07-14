"""Tests documentaires — STARTER-WELCOME-IMAGES-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-images`
(module opt-in `forge-mvc-images`), calquée sur le modèle `welcome-iot` :

- chaque palier pointe vers le suivant (fichier frère dans le dossier de
  niveau) ;
- le dernier palier d'un niveau pointe vers le **bilan du niveau** (`bilan.md`) ;
- le bilan du dernier niveau livré renvoie au `recapitulatif.md` à la racine ;
- aucune commande de création/installation dans les pages de palier
  (`installation.md`, le préambule, en est la seule exception).

Ces assertions grandissent au fil des niveaux livrés (jalon 1 = débutant).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
IMAGES = PROJECT_ROOT / "packages" / "forge-mvc-images" / "docs" / "welcome"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    # STARTERS-WELCOME-INSTALL-001 — `installation.md` est le préambule
    # d'installation, seule page du parcours autorisée à porter les commandes
    # de création/build. Exemptée de l'hygiène « pas de commande de création ».
    return [p for p in IMAGES.rglob("*.md") if p.name != "installation.md"]


# ── Niveau débutant ───────────────────────────────────────────────────────────

class TestDebutantChain:

    def test_images_welcome_points_to_image_upload(self):
        page = IMAGES / "debutant" / "images-welcome.md"
        assert "(image-upload.md)" in page.read_text(encoding="utf-8")

    def test_image_upload_points_to_image_variants(self):
        page = IMAGES / "debutant" / "image-upload.md"
        assert "(image-variants.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # image-variants est le dernier palier débutant.
        page = IMAGES / "debutant" / "image-variants.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_debutant_bilan_points_to_next_level(self):
        # Le niveau intermédiaire existe (jalon 2) → le bilan débutant renvoie
        # à son premier palier.
        bilan = IMAGES / "debutant" / "bilan.md"
        assert "../intermediaire/image-attach.md" in bilan.read_text(encoding="utf-8")


# ── Niveau intermédiaire ──────────────────────────────────────────────────────

class TestIntermediaireChain:

    def test_image_attach_points_to_image_gallery(self):
        page = IMAGES / "intermediaire" / "image-attach.md"
        assert "(image-gallery.md)" in page.read_text(encoding="utf-8")

    def test_image_gallery_points_to_image_alt_order(self):
        page = IMAGES / "intermediaire" / "image-gallery.md"
        assert "(image-alt-order.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # image-alt-order est (pour l'instant) le dernier palier intermédiaire.
        page = IMAGES / "intermediaire" / "image-alt-order.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_intermediaire_bilan_points_to_next_level(self):
        # Le niveau avancé existe (jalon 3) → le bilan intermédiaire renvoie à
        # son premier palier.
        bilan = IMAGES / "intermediaire" / "bilan.md"
        assert "../avance/image-cover.md" in bilan.read_text(encoding="utf-8")


# ── Niveau avancé ─────────────────────────────────────────────────────────────

class TestAvanceChain:

    def test_image_cover_points_to_image_delete(self):
        page = IMAGES / "avance" / "image-cover.md"
        assert "(image-delete.md)" in page.read_text(encoding="utf-8")

    def test_image_delete_points_to_image_safety(self):
        page = IMAGES / "avance" / "image-delete.md"
        assert "(image-safety.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # image-safety est le dernier palier avancé (et de toute la progression).
        page = IMAGES / "avance" / "image-safety.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_avance_bilan_points_to_recapitulatif(self):
        # Dernier niveau → le bilan avancé renvoie au récapitulatif.
        bilan = IMAGES / "avance" / "bilan.md"
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
