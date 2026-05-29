"""Garde-fou OPTINS-PROJECT-STRUCTURE-001.

Vérifie que la page de contrat de la structure opt-in côté projet existe
et verrouille les décisions clés : dossier `optins/`, registre explicite,
distinction package / branchement projet, absence de discovery magique,
indépendance de Forge Core, comparaison Symfony, exemple IoT.

Ticket **documentaire** : ce test lit du texte, il n'exécute aucun code
fonctionnel.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
PAGE = PROJECT_ROOT / "docs" / "architecture" / "optins-project-structure.md"
ROADMAP = PROJECT_ROOT / "docs" / "roadmap" / "forge-roadmap.md"


def _text() -> str:
    return PAGE.read_text(encoding="utf-8")


class TestPageExists:
    def test_page_exists(self):
        assert PAGE.exists(), (
            "docs/architecture/optins-project-structure.md doit exister"
        )


class TestPageContent:
    def test_mentions_optins_dir(self):
        assert "optins/" in _text()

    def test_mentions_registry(self):
        assert "optins/registry.py" in _text()

    def test_distinguishes_package_and_project_branching(self):
        text = _text().lower()
        assert "package opt-in" in text
        assert "branchement projet" in text

    def test_mentions_packages_path(self):
        assert "packages/forge-mvc-" in _text()

    def test_mentions_iot_example(self):
        text = _text()
        assert "Forge IoT" in text
        assert "register_iot_routes" in text

    def test_mentions_optin_routes(self):
        text = _text().lower()
        assert "routes.py" in text
        assert "route" in text

    def test_mentions_optin_migrations(self):
        assert "migration" in _text().lower()

    def test_mentions_local_readme_or_docs(self):
        text = _text()
        assert "README" in text
        assert "documentation locale" in text.lower()


class TestLockedDecisions:
    def test_states_no_magic_discovery(self):
        text = _text().lower()
        assert "discovery magique" in text
        # Et le formule comme un refus explicite.
        assert "pas de discovery magique" in text

    def test_states_core_independent_of_optins(self):
        text = _text().lower()
        # Forge Core ne dépend pas / ne charge pas automatiquement les opt-ins.
        assert "forge core ne dépend pas des opt-ins" in text or (
            "forge core ne charge pas automatiquement" in text
        )

    def test_compares_with_symfony_bundles(self):
        text = _text().lower()
        assert "symfony" in text
        assert "bundle" in text


class TestRoadmapUpdated:
    def test_roadmap_mentions_ticket(self):
        assert "OPTINS-PROJECT-STRUCTURE-001" in ROADMAP.read_text(encoding="utf-8")
