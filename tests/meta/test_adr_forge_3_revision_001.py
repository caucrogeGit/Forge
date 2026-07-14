"""Garde-fou ADR-1-2-FORGE-3-REVISION-001.

Vérifie que les ADR-001 et ADR-002 (Forge 2.x) sont clairement marqués comme
historiques. Un lecteur ne doit pas confondre une stratégie 2.x avec la
stratégie 3.0 courante.

Le contenu décisionnel reste intact — seul un en-tête de statut est ajouté
(principe ADR : on ne modifie pas un ADR a posteriori, on le supersède ou on
l'annote).
"""
from __future__ import annotations

from pathlib import Path

import pytest
pytestmark = [pytest.mark.meta, pytest.mark.docs]

PROJECT_ROOT = Path(__file__).parent.parent.parent

ADR_001 = PROJECT_ROOT / "docs" / "adr" / "001-auth-strategy.md"
ADR_002 = PROJECT_ROOT / "docs" / "adr" / "002-session-strategy.md"

HISTORICAL_ADRS = [ADR_001, ADR_002]

_HISTORICAL_MARKERS = [
    "ADR historique",
    "historique — Forge 2",
    "(Forge 2.x — historique)",
]

_CURRENT_LINKS = [
    "../features/auth.md",
    "../sessions.md",
    "004-core-perimeter.md",
    "charte_philosophique",
]


class TestAdrFiles2xMarkedAsHistorical:
    """ADR-001 et ADR-002 ont un en-tête de statut 'historique' visible."""

    def test_adr_files_exist(self):
        for adr in HISTORICAL_ADRS:
            assert adr.exists(), f"{adr.name} doit exister dans docs/adr/"

    def test_adr_has_historical_marker(self):
        """Chaque ADR 2.x contient un encart 'historique' dans ses 40 premières lignes."""
        for adr in HISTORICAL_ADRS:
            text = adr.read_text(encoding="utf-8")
            header = "\n".join(text.splitlines()[:40])
            found = any(m in header for m in _HISTORICAL_MARKERS)
            assert found, (
                f"{adr.name} doit avoir un marqueur historique dans ses 40 premières "
                f"lignes (ex : '!!! warning \"ADR historique — Forge 2.x\"'). "
                f"Marqueurs acceptés : {_HISTORICAL_MARKERS}"
            )

    def test_adr_points_to_current_state(self):
        """Chaque ADR 2.x pointe vers au moins un document courant dans ses 50 premières lignes."""
        for adr in HISTORICAL_ADRS:
            text = adr.read_text(encoding="utf-8")
            header = "\n".join(text.splitlines()[:50])
            found = any(lnk in header for lnk in _CURRENT_LINKS)
            assert found, (
                f"{adr.name} doit pointer vers au moins un document courant "
                f"dans ses 50 premières lignes. Liens acceptés : {_CURRENT_LINKS}"
            )


class TestAdrContentUnchanged:
    """Le contenu décisionnel des ADR 2.x n'a pas été altéré."""

    def test_adr_001_keeps_decision_section(self):
        text = ADR_001.read_text(encoding="utf-8")
        assert "## Statut" in text or "## Status" in text, (
            "ADR-001 doit conserver sa section Statut."
        )
        assert "## Décision" in text or "## Decision" in text, (
            "ADR-001 doit conserver sa section Décision."
        )

    def test_adr_002_keeps_decision_section(self):
        text = ADR_002.read_text(encoding="utf-8")
        assert "## Statut" in text or "## Status" in text, (
            "ADR-002 doit conserver sa section Statut."
        )
        assert "## Décision" in text or "## Decision" in text, (
            "ADR-002 doit conserver sa section Décision."
        )
