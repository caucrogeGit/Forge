"""Garde-fou RELEASE-BETA12-POST-PUBLISH-VERIFY-001.

Vérifie que l'audit post-publication de Forge 1.0.0-beta.12 existe et
couvre les points attendus du smoke test depuis PyPI : versions
(SemVer + PEP 440), paquet `forge-mvc-iot`, commandes `forge optin:enable
iot` / `forge optin:list`, starter `welcome-iot`, `forge iot:doctor`, et
un verdict explicite.

Audit documentaire : ce test lit du texte, il n'exécute aucune
installation.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT = (
    PROJECT_ROOT / "docs" / "history" / "audits"
    / "audit-beta12-post-publish.md"
)
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return AUDIT.read_text(encoding="utf-8")


class TestAuditExists:
    def test_audit_file_exists(self):
        assert AUDIT.exists(), (
            "docs/history/audits/audit-beta12-post-publish.md doit exister"
        )

    def test_contains_verdict(self):
        text = _text().lower()
        assert "verdict" in text
        # Décision explicite GO / NO-GO.
        assert "go" in text


class TestAuditContent:
    @pytest.mark.parametrize(
        "needle",
        [
            "1.0.0-beta.12",
            "1.0.0b12",
            "forge-mvc-iot",
            "forge optin:enable iot",
            "forge optin:list",
            "welcome-iot",
            "forge iot:doctor",
        ],
    )
    def test_mentions(self, needle):
        assert needle in _text(), f"L'audit doit mentionner {needle!r}"

    def test_mentions_core_independence(self):
        # Le core doit rester indépendant de l'IoT (point clé du smoke test).
        text = _text().lower()
        assert "indépendant" in text


class TestRoadmapUpdated:
    def test_roadmap_mentions_ticket(self):
        assert "RELEASE-BETA12-POST-PUBLISH-VERIFY-001" in ROADMAP.read_text(
            encoding="utf-8"
        )
