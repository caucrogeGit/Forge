"""Tests documentaires — STARTER-WELCOME-IOT-NAV-001.

Verrouille la navigation pédagogique de la progression `welcome-iot`
(module opt-in `forge-mvc-iot`), calquée sur le modèle `welcome-forge` :

- chaque palier pointe vers le suivant (fichier frère dans le dossier de
  niveau) ;
- le dernier palier d'un niveau pointe vers le **bilan du niveau**
  (`bilan.md`, page sœur) ;
- le bilan renvoie au premier palier du niveau suivant s'il existe, sinon
  au `recapitulatif.md` à la racine du starter (STARTERS-DOC-LEVELS) ;
- aucune commande de création/installation interdite dans les pages.

Ces assertions grandissent au fil des paliers livrés.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


PROJECT_ROOT = Path(__file__).parent.parent.parent
IOT = PROJECT_ROOT / "docs" / "starters" / "welcome-iot"

FORBIDDEN_COMMANDS = [
    "forge starter:build",
    "forge new mon-projet",
    "cd mon-projet",
    "source .venv/bin/activate",
]


def _pages() -> list[Path]:
    return list(IOT.rglob("*.md"))


# ── Niveau débutant ───────────────────────────────────────────────────────────

class TestDebutantChain:

    def test_iot_welcome_points_to_iot_events(self):
        page = IOT / "debutant" / "iot-welcome.md"
        assert "(iot-events.md)" in page.read_text(encoding="utf-8")

    def test_last_palier_points_to_level_bilan(self):
        # iot-events est (pour l'instant) le dernier palier débutant.
        page = IOT / "debutant" / "iot-events.md"
        assert "(bilan.md)" in page.read_text(encoding="utf-8")

    def test_debutant_bilan_points_to_recapitulatif(self):
        # Pas encore de niveau intermédiaire → le bilan débutant renvoie au
        # récapitulatif à la racine du starter.
        bilan = IOT / "debutant" / "bilan.md"
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
