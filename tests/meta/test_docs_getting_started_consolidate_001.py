"""Garde-fou DOCS-GETTING-STARTED-CONSOLIDATE-001.

Vérifie que la doc d'installation dispose d'un point d'entrée unique
(docs/guide/getting-started.md) qui oriente vers tous les modes d'installation
et montre la commande de création de premier projet.

Sans ce point d'entrée, le développeur doit deviner quel doc lire en
premier parmi les 6 docs d'installation disponibles.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


GETTING_STARTED = Path("docs/guide/getting-started.md")


class TestGettingStartedExists:
    """docs/guide/getting-started.md existe comme point d'entrée."""

    def test_file_exists(self):
        assert GETTING_STARTED.exists(), (
            f"{GETTING_STARTED} doit exister comme point d'entrée unique "
            "pour les développeurs qui découvrent Forge."
        )

    def test_file_lists_installation_modes(self):
        """Le fichier référence les modes d'installation principaux."""
        text = GETTING_STARTED.read_text(encoding="utf-8")
        required = [
            "install/poste-linux.md",
            "install/github.md",
        ]
        missing = [r for r in required if r not in text]
        assert not missing, (
            f"{GETTING_STARTED} doit lier vers les modes d'installation. "
            f"Manquants : {missing}"
        )

    def test_file_has_first_project_section(self):
        """Le fichier présente la commande forge new pour le premier projet."""
        text = GETTING_STARTED.read_text(encoding="utf-8")
        assert "forge new" in text, (
            f"{GETTING_STARTED} doit montrer la commande `forge new` pour "
            "créer un premier projet."
        )


class TestInstallationDocsConsolidated:
    """Chaque doc d'installation est référencé depuis le point d'entrée."""

    def test_no_orphan_installation_doc(self):
        """Tous les docs installation*.md sont référencés depuis getting-started.md."""
        if not GETTING_STARTED.exists():
            pytest.skip("getting-started.md absent — couvert par TestGettingStartedExists")
        gs_text = GETTING_STARTED.read_text(encoding="utf-8")
        installation_docs = sorted(Path("docs").glob("installation*.md"))
        missing = [
            doc.name for doc in installation_docs
            if doc.name not in gs_text
        ]
        assert not missing, (
            f"Ces docs d'installation ne sont pas référencés depuis "
            f"{GETTING_STARTED} : {missing}. "
            "Soit les ajouter au hub, soit supprimer les fichiers."
        )

    def test_getting_started_in_mkdocs_nav(self):
        """getting-started.md est présent dans la navigation mkdocs.yml."""
        mkdocs = Path("mkdocs.yml").read_text(encoding="utf-8")
        assert "getting-started.md" in mkdocs, (
            "getting-started.md doit apparaître dans la nav de mkdocs.yml."
        )
