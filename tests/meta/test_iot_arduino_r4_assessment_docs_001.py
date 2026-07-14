"""Garde-fou documentaire — IOT-ARDUINO-R4-ASSESSMENT-001.

Vérifie que la page d'évaluation Arduino R4 existe, distingue clairement
évaluation et support officiel, garde l'ESP32 comme cible de référence,
explique les contraintes MQTT/réseau, et ne livre PAS de sketch complet.
Ticket documentation + garde-fou.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAGE = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "arduino-r4-assessment.md"
MKDOCS = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


# ── Présence et référencement ───────────────────────────────────────────────


def test_page_exists():
    assert PAGE.is_file(), "docs/iot/arduino-r4-assessment.md doit exister"


def test_page_referenced_in_mkdocs():
    assert "arduino-r4-assessment.md" in MKDOCS.read_text(encoding="utf-8"), (
        "la page doit être référencée dans la nav mkdocs.yml"
    )


def test_roadmap_mentions_ticket():
    assert "IOT-ARDUINO-R4-ASSESSMENT-001" in ROADMAP.read_text(encoding="utf-8")


# ── Contenu attendu ──────────────────────────────────────────────────────────


class TestMentions:
    @pytest.mark.parametrize("needle", [
        "Arduino R4",
        "ESP32",
        "MQTT",
        "Mosquitto",
    ])
    def test_mentions(self, needle):
        assert needle in _page_text(), f"la page doit mentionner {needle!r}"

    def test_mentions_contract_topic(self):
        assert "forge/{site}/{device_id}/telemetry" in _page_text()

    def test_esp32_is_reference_target(self):
        text = _page_text().lower()
        assert "cible de référence" in text and "esp32" in text, (
            "la page doit garder l'ESP32 comme cible de référence"
        )

    def test_explains_broker_not_localhost(self):
        text = _page_text().lower()
        assert "localhost" in text and "adresse ip" in text, (
            "la page doit expliquer que le broker n'est pas localhost "
            "depuis la carte, mais l'adresse IP du PC/serveur"
        )


# ── Périmètre : évaluation, pas support, pas de sketch complet ──────────────


class TestScope:
    def test_no_complete_sketch(self):
        # Un sketch Arduino complet contiendrait setup() ET loop().
        text = _page_text()
        assert not ("void setup()" in text and "void loop()" in text), (
            "la page ne doit pas fournir de sketch Arduino R4 complet"
        )

    def test_not_officially_supported(self):
        text = _page_text().lower()
        assert (
            "pas encore une cible officielle" in text
            or "ne devient pas encore une cible officielle" in text
            or "pas officiellement" in text
            or "ne supporte pas officiellement" in text
            or "pas de support officiel" in text
        ), (
            "la page ne doit pas prétendre qu'Arduino R4 est officiellement "
            "supporté — elle doit poser le contraire"
        )
