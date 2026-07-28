"""Garde-fou OPTINS-CLI-ENABLE-AUDIT-001.

Vérifie que l'audit de conception de la future commande
`forge optin:enable` existe et verrouille les décisions clés : commande
cible, premier opt-in `iot`, idempotence, `--dry-run`, branchement
explicite via `optins/registry.py`, prudence sur `mvc/routes.py`, refus
de la discovery magique et de l'écrasement silencieux, et le fait que ce
ticket **n'implémente pas** la commande.

Ticket **documentaire** : ce test lit du texte, il n'exécute aucune
commande et ne génère aucun fichier.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAGE = PROJECT_ROOT / "docs" / "architecture" / "optins-cli-enable-audit.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return PAGE.read_text(encoding="utf-8")


class TestPageExists:
    def test_page_exists(self):
        assert PAGE.exists(), (
            "docs/architecture/optins-cli-enable-audit.md doit exister"
        )


class TestCommandContract:
    def test_mentions_command(self):
        assert "forge optin:enable" in _text()

    def test_mentions_iot_as_first_case(self):
        assert "forge optin:enable iot" in _text()

    def test_mentions_dry_run(self):
        assert "--dry-run" in _text()

    def test_mentions_idempotence(self):
        assert "idempoten" in _text().lower()

    def test_mentions_registry(self):
        assert "optins/registry.py" in _text()

    def test_mentions_routes_file(self):
        assert "mvc/routes/__init__.py" in _text()


class TestLockedRules:
    def test_forbids_magic_discovery(self):
        text = _text().lower()
        assert "découverte automatique" in text or "discovery" in text
        # Formulé comme un refus.
        assert "pas de scan automatique" in text or "aucune découverte automatique" in text

    def test_forbids_silent_overwrite(self):
        text = _text().lower()
        assert "écraser silencieusement" in text or "écrasement silencieux" in text

    def test_core_independent_of_optins(self):
        text = _text().lower()
        assert "forge core ne dépend" in text and "opt-in" in text


class TestNonImplementation:
    def test_states_not_implemented_here(self):
        text = _text().lower()
        # Le ticket cadre mais n'implémente pas la commande.
        assert "n'implémente pas" in text or "sans l'implémenter" in text
        # Et pointe vers le ticket d'implémentation.
        assert "OPTINS-CLI-ENABLE-IOT-001" in _text()


class TestRoadmapUpdated:
    def test_roadmap_mentions_ticket(self):
        assert "OPTINS-CLI-ENABLE-AUDIT-001" in ROADMAP.read_text(encoding="utf-8")
