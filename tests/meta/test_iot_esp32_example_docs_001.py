"""Garde-fou documentaire — IOT-ESP32-EXAMPLE-001.

Vérifie que l'exemple ESP32 → MQTT → Forge IoT est présent et complet :
une page `docs/iot/esp32-example.md` et un sketch
`docs/iot/examples/esp32_mqtt_temperature.ino` publiant un message
conforme au contrat. Ticket documentation + exemple, sans code Forge.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAGE = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "esp32-example.md"
SKETCH = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "examples" / "esp32_mqtt_temperature.ino"
MKDOCS = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


def _sketch_text() -> str:
    return SKETCH.read_text(encoding="utf-8")


# ── Présence et référencement ───────────────────────────────────────────────


def test_page_exists():
    assert PAGE.is_file(), "docs/iot/esp32-example.md doit exister"


def test_sketch_exists():
    assert SKETCH.is_file(), (
        "docs/iot/examples/esp32_mqtt_temperature.ino doit exister"
    )


def test_page_referenced_in_mkdocs():
    assert "esp32-example.md" in MKDOCS.read_text(encoding="utf-8"), (
        "la page doit être référencée dans la nav mkdocs.yml"
    )


def test_roadmap_mentions_ticket():
    assert "IOT-ESP32-EXAMPLE-001" in ROADMAP.read_text(encoding="utf-8")


# ── Contenu de la page ───────────────────────────────────────────────────────


class TestPageContent:
    @pytest.mark.parametrize("needle", [
        "ESP32",
        "MQTT",
        "Mosquitto",
        "forge iot:listen",
        "/api/iot/events",
    ])
    def test_mentions(self, needle):
        assert needle in _page_text(), f"la page doit mentionner {needle!r}"

    def test_says_to_adapt_wifi_and_host(self):
        text = _page_text().lower()
        assert "adapter le wi-fi" in text or "adapte" in text, (
            "la page doit indiquer d'adapter le Wi-Fi"
        )
        assert "mqtt_host" in text, (
            "la page doit indiquer d'adapter MQTT_HOST"
        )

    def test_does_not_claim_arduino_r4(self):
        # Arduino R4 doit être explicitement hors périmètre.
        lines = _page_text().lower().splitlines()
        negations = ("hors périmètre", "pas couvert", "non couvert", "dédié")
        disclaimers = [
            line for line in lines
            if "r4" in line and any(neg in line for neg in negations)
        ]
        assert disclaimers, (
            "la page ne doit pas prétendre couvrir Arduino R4 : une ligne "
            "doit le signaler comme hors périmètre"
        )


# ── Contenu du sketch ────────────────────────────────────────────────────────


class TestSketchContent:
    def test_includes_wifi(self):
        assert "WiFi.h" in _sketch_text()

    def test_includes_pubsubclient(self):
        assert "PubSubClient.h" in _sketch_text()

    def test_publishes_on_contract_topic(self):
        assert "forge/atelier/esp32-001/telemetry" in _sketch_text()

    @pytest.mark.parametrize("field", ["kind", "value", "unit", "timestamp"])
    def test_payload_contains_field(self, field):
        assert field in _sketch_text(), (
            f"le payload du sketch doit contenir le champ {field!r}"
        )
