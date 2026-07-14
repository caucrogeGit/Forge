"""Garde-fou BETA12-CLOSING-SUMMARY-001.

Vérifie que l'audit de clôture de la séquence Forge 1.0.0-beta.12 existe et
couvre les points attendus : release PyPI, Forge IoT, opt-ins, site officiel,
landing publique, qualité (0 failed), incidents traités (rsync + rollback),
limites restantes, et verdict de clôture.

Audit documentaire : ce test lit du texte, il n'exécute rien.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT = (
    PROJECT_ROOT / "docs" / "history" / "audits"
    / "audit-beta12-closing-summary.md"
)
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return AUDIT.read_text(encoding="utf-8")


class TestAuditExists:
    def test_audit_file_exists(self):
        assert AUDIT.exists(), (
            "docs/history/audits/audit-beta12-closing-summary.md doit exister"
        )

    def test_contains_verdict(self):
        text = _text().lower()
        assert "verdict" in text
        assert "go" in text


class TestAuditContent:
    @pytest.mark.parametrize(
        "needle",
        [
            "1.0.0-beta.12",
            "forge-mvc-iot",
            "PyPI",
            "forgemvc.com",
            "Forge IoT",
            "optins/",
            "forge optin:enable iot",
            "forge optin:list",
            "iot:doctor",
            "iot:listen",
            "welcome-iot",
            "0 failed",
            "site officiel",
            "rsync",
            "rollback",
            "beta.12 clôturée",
            "roadmap",
        ],
    )
    def test_mentions(self, needle):
        assert needle in _text(), f"L'audit de clôture doit mentionner {needle!r}"

    def test_mentions_incident_rsync(self):
        # L'incident rsync (mauvais dépôt source) doit être tracé.
        text = _text().lower()
        assert "rsync" in text
        assert "forge-official-site" in text

    def test_lists_pypi_packages(self):
        # Les 7 paquets publiés doivent apparaître.
        text = _text()
        for pkg in (
            "forge-mvc-rbac",
            "forge-mvc-workflow",
            "forge-mvc-stats",
            "forge-mvc-mfa",
            "forge-mvc-media",
        ):
            assert pkg in text, f"Paquet publié manquant : {pkg}"


class TestRoadmapUpdated:
    def test_roadmap_mentions_ticket(self):
        assert "BETA12-CLOSING-SUMMARY-001" in ROADMAP.read_text(encoding="utf-8")
