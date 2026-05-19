"""Tests meta — NULLABLE-DOC-FIX-001 : documentation nullable alignée avec ADR-013."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ENTITY_SCHEMA = Path("docs/entities/entity-schema.md")
TYPES = Path("docs/entities/types-forge-mariadb.md")
LIMITES = Path("docs/entities/limites-contrats-json.md")
PIVOTS = Path("docs/entities/pivots-many-to-many.md")
AUDIT = Path("docs/history/audits/nullable-contract-audit-001.md")


# ── entity-schema.md ──────────────────────────────────────────────────────────


def test_entity_schema_mentionne_nullable_defaut_true():
    content = ENTITY_SCHEMA.read_text(encoding="utf-8")
    assert "défaut" in content and "true" in content or "nullable" in content


def test_entity_schema_mentionne_required():
    assert "required" in ENTITY_SCHEMA.read_text(encoding="utf-8")


# ── types-forge-mariadb.md ────────────────────────────────────────────────────


def test_types_mentionne_nullable_par_defaut():
    content = TYPES.read_text(encoding="utf-8")
    assert "par défaut" in content or "défaut" in content


def test_types_mentionne_required_prioritaire():
    content = TYPES.read_text(encoding="utf-8")
    assert "prioritaire" in content or "ADR-013" in content


def test_types_ne_dit_plus_entity_fields_not_null_par_defaut():
    content = TYPES.read_text(encoding="utf-8")
    assert "entity `fields[]`) | `NOT NULL` (défaut implicite)" not in content


def test_types_mentionne_adr_013():
    assert "ADR-013" in TYPES.read_text(encoding="utf-8")


# ── limites-contrats-json.md ──────────────────────────────────────────────────


def test_limites_mentionne_adr_013():
    assert "ADR-013" in LIMITES.read_text(encoding="utf-8")


def test_limites_ne_dit_plus_comportement_different():
    content = LIMITES.read_text(encoding="utf-8")
    assert "comportement différent entre `fields[]` d'entité et `pivot.fields[]`" not in content


# ── pivots-many-to-many.md ────────────────────────────────────────────────────


def test_pivots_mentionne_pivot_fields():
    assert "pivot.fields[]" in PIVOTS.read_text(encoding="utf-8")


def test_pivots_mentionne_required_prioritaire():
    content = PIVOTS.read_text(encoding="utf-8")
    assert "prioritaire" in content or "ADR-013" in content


# ── Audit nullable mis à jour ─────────────────────────────────────────────────


def test_audit_mentionne_nullable_doc_fix_001():
    assert "NULLABLE-DOC-FIX-001" in AUDIT.read_text(encoding="utf-8")
