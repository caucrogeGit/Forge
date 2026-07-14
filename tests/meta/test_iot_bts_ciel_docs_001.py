"""Garde-fou documentaire — IOT-BTS-CIEL-DOCS-001.

Vérifie que la page pédagogique Bac Pro / BTS CIEL existe, explique le
flux IoT complet et propose des activités, sans prétendre couvrir le
matériel réel (Arduino / ESP32). Ticket documentation + garde-fou.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAGE = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "docs" / "bts-ciel.md"
MKDOCS = PROJECT_ROOT / "packages" / "forge-mvc-iot" / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


# ── Présence et référencement ───────────────────────────────────────────────


def test_page_exists():
    assert PAGE.is_file(), "docs/iot/bts-ciel.md doit exister"


def test_page_referenced_in_mkdocs():
    assert "bts-ciel.md" in MKDOCS.read_text(encoding="utf-8"), (
        "la page doit être référencée dans la nav mkdocs.yml"
    )


def test_roadmap_mentions_ticket():
    assert "IOT-BTS-CIEL-DOCS-001" in ROADMAP.read_text(encoding="utf-8")


# ── Contenu attendu ──────────────────────────────────────────────────────────


class TestMentions:
    @pytest.mark.parametrize("needle", [
        "Bac Pro",
        "BTS CIEL",
        "MQTT",
        "Mosquitto",
        "forge iot:simulate",
        "forge iot:listen",
        "/api/iot/events",
        "iot_events",
    ])
    def test_mentions(self, needle):
        assert needle in _page_text(), f"la page doit mentionner {needle!r}"

    def test_explains_topic(self):
        assert "forge/{site}/{device_id}/telemetry" in _page_text(), (
            "la page doit expliquer le format de topic canonique"
        )

    def test_has_at_least_one_activity(self):
        assert "Activité 1" in _page_text(), (
            "la page doit proposer au moins une activité pédagogique"
        )


# ── Périmètre : matériel réel non couvert ────────────────────────────────────


class TestScopeNotOverclaimed:
    _NEGATIONS = (
        "hors périmètre",
        "pas couvert",
        "non couvert",
        "plus tard",
        "ultérieur",
        "à venir",
    )

    def test_does_not_claim_real_hardware(self):
        # Le matériel réel (Arduino / ESP32 réel) doit être explicitement
        # signalé comme non couvert : on cherche une ligne qui mentionne
        # « arduino » avec un marqueur « hors périmètre / non couvert ».
        # (Le device_id d'exemple « esp32-001 » n'est pas une prétention
        # de couverture matérielle — on cible donc « arduino ».)
        lines = _page_text().lower().splitlines()
        disclaimers = [
            line for line in lines
            if "arduino" in line and any(neg in line for neg in self._NEGATIONS)
        ]
        assert disclaimers, (
            "la page doit indiquer explicitement que le capteur réel "
            "(Arduino / ESP32 réel) n'est pas couvert"
        )
