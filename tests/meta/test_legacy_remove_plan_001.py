"""Garde-fou documentaire LEGACY-REMOVE-PLAN-001.

Vérifie que le rapport d'audit du plan de suppression accélérée du legacy Forge
existe et contient les éléments attendus.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

REPORT = Path(__file__).resolve().parent.parent.parent / "docs" / "history" / "audits" / "legacy-remove-plan-001.md"


def _content() -> str:
    return REPORT.read_text(encoding="utf-8")


def test_rapport_existe():
    assert REPORT.exists()


def test_rapport_mentionne_format_version():
    assert "format_version" in _content()


def test_rapport_mentionne_schema_version():
    assert "schema_version" in _content()


def test_rapport_mentionne_sql_type():
    assert "sql_type" in _content()


def test_rapport_mentionne_from_entity():
    assert "from_entity" in _content()


def test_rapport_mentionne_suppression_acceleree():
    assert "suppression accélérée" in _content()


def test_rapport_mentionne_aucune_application_reelle():
    assert "aucune application réelle" in _content().lower() or \
           "Aucune application réelle" in _content()


def test_rapport_propose_legacy_remove_001():
    assert "LEGACY-REMOVE-001" in _content()


def test_rapport_propose_legacy_remove_002():
    assert "LEGACY-REMOVE-002" in _content()


def test_rapport_propose_legacy_close_001():
    assert "LEGACY-CLOSE-001" in _content()


def test_rapport_ne_dit_pas_que_suppression_est_faite():
    content = _content()
    assert "suppression est faite" not in content
    assert "suppression a été effectuée" not in content
    assert "Aucune suppression n'a été effectuée" in content
