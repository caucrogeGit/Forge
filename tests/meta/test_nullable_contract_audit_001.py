"""Tests meta — NULLABLE-CONTRACT-001 : audit du comportement nullable dans les contrats JSON."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

AUDIT = Path("docs/history/audits/nullable-contract-audit-001.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_audit_existe():
    assert AUDIT.exists()


# ── Contenu obligatoire ────────────────────────────────────────────────────────


def test_audit_mentionne_nullable():
    assert "nullable" in _audit()


def test_audit_mentionne_required():
    assert "required" in _audit()


def test_audit_mentionne_fields():
    content = _audit()
    assert "fields[]" in content


def test_audit_mentionne_pivot_fields():
    content = _audit()
    assert "pivot.fields[]" in content or "pivot.fields" in content


def test_audit_mentionne_field_schema_json():
    assert "field.schema.json" in _audit()


def test_audit_mentionne_null():
    assert "NULL" in _audit()


def test_audit_mentionne_not_null():
    assert "NOT NULL" in _audit()


# ── Options de correction ──────────────────────────────────────────────────────


def test_audit_mentionne_options_correction():
    content = _audit()
    assert "Option A" in content
    assert "Option B" in content


def test_audit_propose_nullable_contract_002():
    assert "NULLABLE-CONTRACT-002" in _audit()


# ── Garde-fous ────────────────────────────────────────────────────────────────


def test_audit_ne_dit_pas_correction_appliquee():
    content = _audit()
    assert "correction appliquée" not in content
    assert "comportement corrigé" not in content
