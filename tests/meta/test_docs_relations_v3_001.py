"""Garde-fous DOCS-RELATIONS-MD-REFRESH-001 : cohérence de docs/features/relations.md avec Forge 3.0.

Les mentions du champ technique `format_version: 1` et les jalons historiques
("depuis Forge 1.5.0") restent autorisés — seules les affirmations d'état actuel
obsolètes (version Forge comme état courant) sont interdites.
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
RELATIONS_PATH = PROJECT_ROOT / "docs" / "features" / "relations.md"


class TestRelationsMdNoStaleForgeVersion:
    """Aucune mention de version Forge comme état actuel courant."""

    def test_file_exists(self):
        assert RELATIONS_PATH.exists(), "docs/features/relations.md introuvable"

    def test_no_stale_current_state_1_5_0(self):
        text = RELATIONS_PATH.read_text(encoding="utf-8")
        assert "tel qu'il existe dans Forge 1.5.0" not in text, (
            "docs/features/relations.md présente encore Forge 1.5.0 comme version actuelle — "
            "mettre à jour l'en-tête de page"
        )

    def test_no_forge_v1_as_framework_qualifier(self):
        text = RELATIONS_PATH.read_text(encoding="utf-8")
        assert "Forge V1" not in text, (
            "docs/features/relations.md utilise 'Forge V1' comme qualificatif de version du framework — "
            "remplacer par 'Le système de relations' ou équivalent neutre"
        )


class TestRelationsMdFormatVersionLegitimate:
    """Les mentions du champ technique format_version restent présentes."""

    def test_format_version_still_present(self):
        text = RELATIONS_PATH.read_text(encoding="utf-8")
        assert "format_version" in text, (
            "docs/features/relations.md doit toujours documenter le champ format_version "
            "(version du format de fichier relations.json — distincte de la version Forge)"
        )
