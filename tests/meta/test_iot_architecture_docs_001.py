"""Garde-fou IOT-ARCHITECTURE-001.

Vérifie que la page fondatrice ``docs/iot/architecture.md`` existe, est
référencée dans la navigation MkDocs, et verrouille la séparation entre
Forge Core, ``forge-mvc-iot``, le broker MQTT et Forge Design IoT.

Ce test est documentaire : il ne contraint pas l'implémentation du
module ``forge-mvc-iot`` (qui n'existe pas encore). Il garantit
uniquement que les décisions d'architecture restent visibles dans la
documentation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent

ARCHITECTURE_PAGE = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "architecture.md"
MKDOCS_YML = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "mkdocs.yml"

FOLLOW_UP_TICKETS = (
    "IOT-PACKAGE-SCAFFOLD-001",
    "IOT-MQTT-CONTRACT-001",
    "IOT-MQTT-SUBSCRIBER-001",
    "IOT-CONFIG-001",
    "IOT-STORAGE-EVENTS-001",
    "IOT-HTTP-API-001",
    "IOT-DOCTOR-001",
    "IOT-STARTER-MQTT-HELLO-001",
    "FORGE-DESIGN-IOT-READ-API-001",
)


class TestArchitecturePageExists:
    def test_file_present(self):
        assert ARCHITECTURE_PAGE.exists(), (
            f"{ARCHITECTURE_PAGE.relative_to(PROJECT_ROOT)} doit exister"
        )

    def test_file_not_empty(self):
        text = ARCHITECTURE_PAGE.read_text(encoding="utf-8")
        assert len(text) > 1000, (
            "La page d'architecture IoT doit être substantielle (> 1000 caractères)."
        )


class TestArchitecturePageReferencedInNav:
    def test_listed_in_mkdocs_yml(self):
        text = MKDOCS_YML.read_text(encoding="utf-8")
        assert "architecture.md" in text, (
            "docs/iot/architecture.md doit être référencé dans mkdocs.yml"
        )

    def test_iot_section_present_in_nav(self):
        text = MKDOCS_YML.read_text(encoding="utf-8")
        assert "Progression IoT:" in text, (
            "La navigation MkDocs doit contenir la section IoT (sous-mkdocs du paquet, ADR-038)"
        )


class TestArchitecturePageContent:
    def setup_method(self):
        self.text = ARCHITECTURE_PAGE.read_text(encoding="utf-8")

    def test_mentions_forge_mvc_iot(self):
        assert "forge-mvc-iot" in self.text

    def test_mentions_mosquitto(self):
        assert "Mosquitto" in self.text

    def test_mentions_mqtt(self):
        assert "MQTT" in self.text

    def test_affirms_forge_core_autonomous(self):
        # Une formulation explicite indiquant que Forge Core ne dépend
        # pas du module IoT doit être présente.
        assert "Forge Core ne dépend pas de" in self.text, (
            "La page doit affirmer que Forge Core ne dépend pas de forge-mvc-iot"
        )

    def test_affirms_iot_depends_on_core(self):
        assert "dépend de Forge Core" in self.text, (
            "La page doit affirmer que forge-mvc-iot dépend de Forge Core"
        )

    def test_affirms_design_reads_api(self):
        # Forge Design IoT consomme l'API Forge — pas le broker.
        assert "API Forge" in self.text, (
            "La page doit indiquer que Forge Design IoT lit l'API Forge"
        )

    def test_does_not_claim_design_reads_broker(self):
        # Aucune phrase n'affirme que Forge Design IoT lit directement
        # Mosquitto ou le broker. Décision verrouillée par ce ticket.
        forbidden = (
            "Forge Design IoT lit directement",
            "Forge Design IoT lit Mosquitto",
            "Forge Design IoT lit le broker",
            "Forge Design IoT se connecte au broker",
        )
        for needle in forbidden:
            assert needle not in self.text, (
                f"Formulation interdite trouvée : {needle!r}. Forge Design IoT "
                "ne doit jamais lire le broker directement."
            )


class TestFollowUpTicketsListed:
    """Les tickets jalons doivent rester visibles en fin de page."""

    def setup_method(self):
        self.text = ARCHITECTURE_PAGE.read_text(encoding="utf-8")

    @pytest.mark.parametrize("ticket", FOLLOW_UP_TICKETS)
    def test_ticket_listed(self, ticket: str):
        assert ticket in self.text, (
            f"Le ticket {ticket} doit apparaître dans la liste des tickets suivants"
        )
