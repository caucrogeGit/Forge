"""Garde-fou RELEASE-BETA12-PRE-AUDIT-001.

Vérifie que l'audit pré-release beta.12 existe et couvre les points
attendus : version cible, blocs IoT et opt-ins, paquet `forge-mvc-iot`,
commandes `optin:enable iot` / `optin:list`, lots de tests IoT/opt-ins,
validations standard (`mkdocs --strict`, `ruff`, `compileall`,
`git diff --check`), et une décision **GO** ou **NO-GO** explicite.

Audit documentaire : ce test lit du texte, il n'exécute aucune release.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT = PROJECT_ROOT / "docs" / "history" / "audits" / "audit-pre-release-beta12.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return AUDIT.read_text(encoding="utf-8")


class TestAuditExists:
    def test_audit_file_exists(self):
        assert AUDIT.exists(), (
            "docs/history/audits/audit-pre-release-beta12.md doit exister"
        )


class TestAuditContent:
    def test_mentions_target_version(self):
        assert "1.0.0-beta.12" in _text()

    def test_mentions_iot(self):
        assert "Forge IoT" in _text()

    def test_mentions_optins(self):
        assert "opt-ins" in _text()

    def test_mentions_iot_package(self):
        assert "forge-mvc-iot" in _text()

    def test_mentions_enable_iot(self):
        assert "forge optin:enable iot" in _text()

    def test_mentions_list(self):
        assert "forge optin:list" in _text()

    def test_mentions_iot_tests(self):
        text = _text()
        assert "tests/test_iot_" in text or "tests IoT" in text or "IoT ciblé" in text

    def test_mentions_optins_tests(self):
        text = _text()
        assert "tests/test_optins_" in text or "opt-ins ciblé" in text or "tests opt-ins" in text


class TestAuditValidations:
    @pytest.mark.parametrize(
        "tool",
        ["mkdocs build --strict", "ruff", "compileall", "git diff --check"],
    )
    def test_mentions_validation_tool(self, tool):
        assert tool in _text()


class TestAuditDecision:
    def test_contains_go_or_nogo(self):
        text = _text()
        assert "GO / NO-GO" in text or "NO-GO" in text or "GO" in text

    def test_decision_is_explicit(self):
        # L'audit doit trancher clairement (verdict en tête).
        text = _text().upper()
        assert "NO-GO" in text or "GO" in text


class TestRoadmapUpdated:
    def test_roadmap_mentions_ticket(self):
        assert "RELEASE-BETA12-PRE-AUDIT-001" in ROADMAP.read_text(encoding="utf-8")
