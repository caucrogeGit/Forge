"""Tests meta — ENTITY-SCHEMA-RBAC-001 : décision de non-intégration de rbac.

Vérifie que le document d'audit est présent, mentionne les éléments clés
de l'audit et reflète la décision de non-intégration dans entity.schema.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT = Path("docs/history/audits/entity-schema-rbac-decision-001.md")
ENTITY_SCHEMA = Path("cli/schemas/entity.schema.json")


def _text() -> str:
    return AUDIT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_audit_existe():
    assert AUDIT.exists()


# ── Contenu de l'audit ────────────────────────────────────────────────────────


def test_audit_mentionne_ticket():
    assert "ENTITY-SCHEMA-RBAC-001" in _text()


def test_audit_mentionne_entity_schema():
    assert "entity.schema.json" in _text()


def test_audit_mentionne_validation_py():
    assert "validation.py" in _text()


def test_audit_mentionne_normalizer():
    text = _text()
    assert "canonical_model_normalizer" in text or "normaliz" in text.lower()


def test_audit_mentionne_option_a():
    assert "Option A" in _text()


def test_audit_mentionne_option_b():
    assert "Option B" in _text()


def test_audit_mentionne_decision():
    text = _text()
    assert "Décision" in text or "décision" in text


# ── Décision correcte ─────────────────────────────────────────────────────────


def test_audit_decision_non_integration():
    text = _text()
    assert "Option A retenue" in text or "non-intégration" in text.lower() or "non intégration" in text.lower()


def test_audit_ne_dit_pas_rbac_integre_dans_schema():
    text = _text()
    assert "rbac intégré dans entity.schema.json" not in text


def test_audit_mentionne_ticket_suivant():
    text = _text()
    assert "ENTITY-SCHEMA-RBAC-002" in text or "ticket suivant" in text.lower()


# ── État du schéma canonique ─────────────────────────────────────────────────


def test_entity_schema_existe():
    assert ENTITY_SCHEMA.exists()


def test_entity_schema_pas_de_propriete_rbac():
    schema = json.loads(ENTITY_SCHEMA.read_text(encoding="utf-8"))
    assert "rbac" not in schema.get("properties", {})


def test_entity_schema_additional_properties_false():
    schema = json.loads(ENTITY_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("additionalProperties") is False
