"""Garde-fou OPTINS-CLOSING-AUDIT-001.

Vérifie que l'audit de clôture du chantier opt-ins existe et couvre les
points attendus : verdict, structure `optins/`, packages distribués,
commandes `optin:enable iot` / `optin:list`, dry-run / `--apply`,
idempotence, refus de la discovery magique et de l'écrasement silencieux,
`welcome-iot`, `mvc/routes.py`, `iot` comme seul opt-in supporté, limites
et tickets reportés.

Audit **documentaire** : ce test lit du texte, il n'exécute aucune
commande.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
AUDIT = PROJECT_ROOT / "docs" / "history" / "audits" / "audit-optins-closing.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return AUDIT.read_text(encoding="utf-8")


class TestAuditExists:
    def test_audit_file_exists(self):
        assert AUDIT.exists(), (
            "docs/history/audits/audit-optins-closing.md doit exister"
        )

    def test_has_verdict_and_decision(self):
        text = _text().lower()
        assert "verdict" in text
        assert "clôture" in text or "cloture" in text


class TestAuditContent:
    def test_mentions_optins_structure(self):
        assert "optins/" in _text()

    def test_mentions_distributed_packages(self):
        assert "packages/forge-mvc-" in _text()

    def test_mentions_enable_iot(self):
        assert "forge optin:enable iot" in _text()

    def test_mentions_list(self):
        assert "forge optin:list" in _text()

    def test_mentions_dry_run_and_apply(self):
        text = _text()
        assert "dry-run" in text.lower()
        assert "--apply" in text

    def test_mentions_idempotence(self):
        assert "idempoten" in _text().lower()

    def test_mentions_welcome_iot(self):
        assert "welcome-iot" in _text()

    def test_mentions_routes_file(self):
        assert "mvc/routes.py" in _text()


class TestLockedRules:
    def test_no_magic_discovery(self):
        assert "pas de discovery magique" in _text().lower()

    def test_no_silent_overwrite(self):
        text = _text().lower()
        assert "écrasement silencieux" in text

    def test_iot_only_supported(self):
        text = _text().lower()
        # L'audit doit dire clairement que seul iot est supporté.
        assert "seul `iot` est supporté" in text or "seul iot est supporté" in text


class TestLimitsAndDeferred:
    def test_mentions_limits(self):
        assert "limites" in _text().lower()

    @pytest.mark.parametrize(
        "ticket",
        [
            "OPTINS-CLI-ENABLE-RBAC-AUDIT-001",
            "OPTINS-CLI-ENABLE-MEDIA-AUDIT-001",
            "OPTINS-CLI-DISABLE-AUDIT-001",
            "OPTINS-CLI-LIST-JSON-001",
            "OPTINS-CONFLICT-REPORT-001",
        ],
    )
    def test_lists_deferred_tickets(self, ticket):
        assert ticket in _text()


class TestRoadmapUpdated:
    def test_roadmap_mentions_closing_audit(self):
        assert "OPTINS-CLOSING-AUDIT-001" in ROADMAP.read_text(encoding="utf-8")
