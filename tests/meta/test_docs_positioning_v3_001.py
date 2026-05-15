"""Garde-fous DOCS-POSITIONING-V3-001 : cohérence de docs/positioning.md avec la version courante."""
from __future__ import annotations

import tomllib
from pathlib import Path

import pytest
pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent
POSITIONING = PROJECT_ROOT / "docs" / "positioning.md"


def _current_major_minor() -> str:
    data = tomllib.loads((PROJECT_ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    parts = data["project"]["version"].split(".")
    return f"{parts[0]}.{parts[1]}"


class TestPositioningV3:
    """docs/positioning.md ne contient pas d'affirmation de stabilité sur une version antérieure."""

    def test_positioning_exists(self):
        assert POSITIONING.exists(), "docs/positioning.md introuvable"

    def test_no_v1_stable_claim(self):
        text = POSITIONING.read_text(encoding="utf-8")
        assert "V1.0 est stable" not in text, (
            "docs/positioning.md affirme encore que 'V1.0 est stable' — "
            "mettre à jour vers l'état réel du projet"
        )

    def test_no_stale_v1_version_claim(self):
        text = POSITIONING.read_text(encoding="utf-8")
        assert "La V1.0" not in text, (
            "docs/positioning.md contient encore 'La V1.0' — "
            "la mention de version doit refléter l'état courant"
        )

    def test_mentions_current_generation(self):
        major_minor = _current_major_minor()
        text = POSITIONING.read_text(encoding="utf-8")
        assert major_minor in text, (
            f"docs/positioning.md ne mentionne pas la génération courante "
            f"({major_minor}) — la page de positionnement doit refléter l'état courant"
        )
