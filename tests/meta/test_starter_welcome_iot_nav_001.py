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

pytestmark = [pytest.mark.meta, pytest.mark.docs]


PROJECT_ROOT = Path(__file__).parent.parent.parent
# Doc embarquée par paquet depuis l'ADR-038.
IOT = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "welcome"

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
    return [p for p in IOT.rglob("*.md") if p.name != "installation.md"]


# ── Niveau débutant ───────────────────────────────────────────────────────────

class TestDebutantChain:

    def test_iot_welcome_points_to_iot_events(self):
        page = IOT / "debutant" / "iot-welcome.md"
        assert "(iot-events.md)" in page.read_text(encoding="utf-8")

    def test_iot_events_points_to_iot_device(self):
        page = IOT / "debutant" / "iot-events.md"
        assert "(iot-device.md)" in page.read_text(encoding="utf-8")

    # Le « dernier palier mène au bilan » figeait une page nommée. La
    # propriété est dérivée du `nav` par le contrôle partagé
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_debutant_bilan_points_to_next_level(self):
        # Le niveau intermédiaire existe → le bilan débutant renvoie à son
        # premier palier.
        bilan = IOT / "debutant" / "bilan.md"
        assert "../intermediaire/iot-simulate.md" in bilan.read_text(encoding="utf-8")


# ── Niveau intermédiaire ──────────────────────────────────────────────────────

class TestIntermediaireChain:

    def test_iot_simulate_points_to_iot_api(self):
        page = IOT / "intermediaire" / "iot-simulate.md"
        assert "(iot-api.md)" in page.read_text(encoding="utf-8")

    def test_iot_api_points_to_iot_dashboard(self):
        page = IOT / "intermediaire" / "iot-api.md"
        assert "(iot-dashboard.md)" in page.read_text(encoding="utf-8")

    # Le « dernier palier mène au bilan » figeait une page nommée. La
    # propriété est dérivée du `nav` par le contrôle partagé
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_intermediaire_bilan_points_to_next_level(self):
        # Le niveau avancé existe → le bilan intermédiaire renvoie à son
        # premier palier.
        bilan = IOT / "intermediaire" / "bilan.md"
        assert "../avance/iot-contract.md" in bilan.read_text(encoding="utf-8")


# ── Niveau avancé ─────────────────────────────────────────────────────────────

class TestAvanceChain:

    def test_iot_contract_points_to_iot_subscriber(self):
        page = IOT / "avance" / "iot-contract.md"
        assert "(iot-subscriber.md)" in page.read_text(encoding="utf-8")

    def test_iot_subscriber_points_to_iot_doctor(self):
        page = IOT / "avance" / "iot-subscriber.md"
        assert "(iot-doctor.md)" in page.read_text(encoding="utf-8")

    # Le « dernier palier mène au bilan » figeait une page nommée. La
    # propriété est dérivée du `nav` par le contrôle partagé
    # (`WELCOME-CHAINES-DERIVEES-001`).

    def test_avance_bilan_points_to_recapitulatif(self):
        # Dernier niveau → le bilan avancé renvoie au récapitulatif.
        bilan = IOT / "avance" / "bilan.md"
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
