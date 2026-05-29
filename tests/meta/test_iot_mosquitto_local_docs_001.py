"""Garde-fou documentaire — IOT-MOSQUITTO-LOCAL-DOCS-001.

Vérifie que la page `docs/iot/mosquitto-local.md` documente le flux IoT
local complet et reste dans son périmètre (broker local, sans TLS/auth/
cloud). Aucun code fonctionnel n'est testé ici : ce ticket est
documentation + garde-fou.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAGE = PROJECT_ROOT / "docs" / "iot" / "mosquitto-local.md"
MKDOCS = PROJECT_ROOT / "mkdocs.yml"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _page_text() -> str:
    return PAGE.read_text(encoding="utf-8")


# ── Présence et référencement ───────────────────────────────────────────────


def test_page_exists():
    assert PAGE.is_file(), "docs/iot/mosquitto-local.md doit exister"


def test_page_referenced_in_mkdocs():
    assert "iot/mosquitto-local.md" in MKDOCS.read_text(encoding="utf-8"), (
        "la page doit être référencée dans la nav mkdocs.yml"
    )


def test_roadmap_mentions_ticket():
    assert "IOT-MOSQUITTO-LOCAL-DOCS-001" in ROADMAP.read_text(encoding="utf-8")


# ── Contenu attendu ──────────────────────────────────────────────────────────


class TestMentionsCommands:
    @pytest.mark.parametrize("needle", [
        "mosquitto",
        "mosquitto_pub",
        "mosquitto_sub",
        "forge iot:doctor --mqtt",
        "forge iot:init",
        "forge migration:apply",
        "forge iot:listen",
        "forge iot:simulate",
        "/api/iot/events",
    ])
    def test_mentions(self, needle):
        assert needle in _page_text(), f"la page doit mentionner {needle!r}"

    def test_recalls_topic_contract(self):
        assert "forge/{site}/{device_id}/telemetry" in _page_text(), (
            "la page doit rappeler le format de topic canonique"
        )


# ── Périmètre : TLS / auth / cloud présentés comme NON couverts ─────────────


class TestScopeNotOverclaimed:
    # Marqueurs qui indiquent « pas couvert par cette page ».
    _NEGATIONS = (
        "hors périmètre",
        "pas couvert",
        "pas couverte",
        "non couvert",
        "plus tard",
        "ultérieur",
        "pas de tls",
        "sans tls",
    )

    @pytest.mark.parametrize("topic", ["tls", "cloud", "authentif"])
    def test_topic_only_in_not_covered_context(self, topic):
        # Chaque ligne mentionnant TLS / cloud / authentification doit
        # aussi porter un marqueur « non couvert » : la page ne doit pas
        # laisser croire que ces sujets sont traités ici.
        for raw_line in _page_text().splitlines():
            line = raw_line.lower()
            if topic in line:
                assert any(neg in line for neg in self._NEGATIONS), (
                    f"La ligne mentionnant {topic!r} doit indiquer que ce "
                    f"sujet n'est pas couvert par cette page : {raw_line!r}"
                )
