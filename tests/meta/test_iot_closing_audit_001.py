"""Garde-fou IOT-CLOSING-AUDIT-001.

Vérifie que l'audit de clôture Forge IoT existe et couvre les points
attendus : verdict, paquet opt-in, les 4 commandes CLI, MQTT/Mosquitto,
stockage `iot_events`, API HTTP + Bearer token, TLS, pédagogie
(welcome-iot, BTS CIEL, ESP32, Arduino R4 non officiel), limites
assumées, et le chantier reporté `OPTINS-PROJECT-STRUCTURE-001`.

Audit **documentaire** : ce test lit du texte, il n'exécute aucun flux
IoT.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT = PROJECT_ROOT / "docs" / "history" / "audits" / "audit-iot-closing.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _audit_text() -> str:
    return AUDIT.read_text(encoding="utf-8")


class TestAuditExists:
    def test_audit_file_exists(self):
        assert AUDIT.exists(), "docs/history/audits/audit-iot-closing.md doit exister"

    def test_audit_has_verdict_and_decision(self):
        text = _audit_text().lower()
        assert "verdict" in text
        assert "clôture" in text or "cloture" in text


class TestAuditContent:
    def test_mentions_optin_package(self):
        assert "forge-mvc-iot" in _audit_text()

    @pytest.mark.parametrize(
        "command",
        ["iot:doctor", "iot:init", "iot:listen", "iot:simulate"],
    )
    def test_mentions_each_command(self, command):
        assert command in _audit_text()

    @pytest.mark.parametrize("option", ["--db", "--mqtt", "--profile"])
    def test_mentions_cli_options(self, option):
        assert option in _audit_text()

    def test_mentions_mqtt_and_mosquitto(self):
        text = _audit_text()
        assert "MQTT" in text
        assert "Mosquitto" in text

    def test_mentions_storage_table(self):
        assert "iot_events" in _audit_text()

    def test_mentions_http_api(self):
        text = _audit_text()
        assert "API HTTP" in text
        assert "/api/iot/events" in text

    def test_mentions_bearer_token(self):
        assert "Bearer token" in _audit_text()

    def test_mentions_tls(self):
        assert "TLS" in _audit_text()

    def test_mentions_pedagogy(self):
        text = _audit_text()
        assert "welcome-iot" in text
        assert "BTS CIEL" in text
        assert "ESP32" in text

    def test_arduino_r4_marked_not_official(self):
        text = _audit_text()
        assert "Arduino R4" in text
        lowered = text.lower()
        # L'audit doit dire clairement que l'Arduino R4 n'est pas officiel.
        assert "non supporté officiellement" in lowered or (
            "arduino r4" in lowered and "non" in lowered and "officiel" in lowered
        )


class TestAuditLimitsAndDebt:
    def test_mentions_limits(self):
        text = _audit_text().lower()
        assert "limites" in text
        # Quelques limites clés explicitement assumées.
        assert "rétention" in text or "retention" in text
        assert "downlink" in text

    def test_mentions_deferred_optins_chantier(self):
        text = _audit_text()
        assert "OPTINS-PROJECT-STRUCTURE-001" in text
        # Doit être présenté comme reporté / non commencé.
        assert "report" in text.lower()


class TestRoadmapUpdated:
    def test_roadmap_mentions_closing_audit(self):
        assert "IOT-CLOSING-AUDIT-001" in ROADMAP.read_text(encoding="utf-8")
