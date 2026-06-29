"""Tests meta — RBAC-CONTRACT-001 : contrat RBAC séparé du schéma d'entité.

Vérifie que l'ADR-014 est présent, cohérent avec la décision de non-intégration
dans entity.schema.json, et que le rapport ENTITY-SCHEMA-RBAC-001 ne recommande
plus une intégration dans entity.schema.json.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ADR = Path("docs/adr/014-rbac-contract-location.md")
ENTITY_SCHEMA = Path("cli/schemas/entity.schema.json")
AUDIT_PREV = Path("docs/history/audits/entity-schema-rbac-decision-001.md")


def _adr() -> str:
    return ADR.read_text(encoding="utf-8")


def _audit() -> str:
    return AUDIT_PREV.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_adr_014_existe():
    assert ADR.exists()


# ── Contenu de l'ADR ──────────────────────────────────────────────────────────


def test_adr_mentionne_rbac():
    assert "rbac" in _adr().lower() or "RBAC" in _adr()


def test_adr_mentionne_entity_schema():
    assert "entity.schema.json" in _adr()


def test_adr_rbac_hors_schema_entite():
    text = _adr()
    assert "ne sera pas intégré" in text or "hors" in text.lower() or "séparé" in text.lower()


def test_adr_mentionne_emplacement_separe():
    assert "mvc/security/rbac.json" in _adr()


def test_adr_mentionne_permissions():
    assert "permissions" in _adr().lower()


def test_adr_mentionne_roles():
    text = _adr()
    assert "roles" in text.lower() or "rôles" in text.lower()


# ── Schéma canonique inchangé ─────────────────────────────────────────────────


def test_entity_schema_pas_de_propriete_rbac():
    schema = json.loads(ENTITY_SCHEMA.read_text(encoding="utf-8"))
    assert "rbac" not in schema.get("properties", {})


def test_entity_schema_additional_properties_false():
    schema = json.loads(ENTITY_SCHEMA.read_text(encoding="utf-8"))
    assert schema.get("additionalProperties") is False


# ── Rapport précédent corrigé ─────────────────────────────────────────────────


def test_audit_ne_recommande_plus_integration_entity_schema():
    text = _audit()
    assert "ENTITY-SCHEMA-RBAC-002" not in text


def test_audit_recommande_rbac_contract_001():
    text = _audit()
    assert "RBAC-CONTRACT-001" in text


# ── Absence de publication ─────────────────────────────────────────────────────


def test_adr_ne_mentionne_pas_pypi_publie():
    text = _adr()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
    assert "forge-mvc publié" not in text
