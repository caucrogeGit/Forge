"""Tests meta — LEGACY-CLOSE-001 : clôture du bloc de suppression legacy.

Vérifie que le document d'audit mentionne tous les tickets livrés et reflète
l'état final attendu du bloc legacy.
"""

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PLAN = Path("docs/history/audits/legacy-remove-plan-001.md")


def _text() -> str:
    return PLAN.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_legacy_remove_plan_existe():
    assert PLAN.exists()


# ── Tickets livrés ────────────────────────────────────────────────────────────


def test_plan_mentionne_legacy_close_001():
    assert "LEGACY-CLOSE-001" in _text()


def test_plan_mentionne_legacy_remove_001a():
    assert "LEGACY-REMOVE-001A" in _text()


def test_plan_mentionne_legacy_remove_001b():
    assert "LEGACY-REMOVE-001B" in _text()


def test_plan_mentionne_legacy_remove_002():
    assert "LEGACY-REMOVE-002" in _text()


def test_plan_mentionne_legacy_remove_003():
    assert "LEGACY-REMOVE-003" in _text()


def test_plan_mentionne_legacy_remove_004():
    assert "LEGACY-REMOVE-004" in _text()


def test_plan_mentionne_legacy_strict_schema_001():
    assert "LEGACY-STRICT-SCHEMA-001" in _text()


# ── État final ────────────────────────────────────────────────────────────────


def test_plan_mentionne_schema_version_obligatoire():
    text = _text()
    assert 'schema_version: "1.0"' in text or "schema_version obligatoire" in text


def test_plan_mentionne_format_version_refuse():
    text = _text()
    assert "format_version" in text and "refusé" in text


def test_plan_mentionne_relations_json():
    assert "relations.json" in _text()


def test_plan_mentionne_starters_canoniques():
    text = _text()
    assert "starter" in text.lower() and "canonique" in text.lower()


# ── Absence de publication ─────────────────────────────────────────────────────


def test_plan_ne_dit_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "forge-mvc publié" not in text
    assert "publié sur PyPI" not in text


def test_plan_ne_dit_pas_tag_cree():
    text = _text()
    assert "tag créé" not in text
    assert "nouveau tag" not in text
