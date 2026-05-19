"""Tests meta — NULLABLE-CLOSE-001 : clôture du bloc nullable / required."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

AUDIT = Path("docs/history/audits/nullable-contract-audit-001.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_audit_existe():
    assert AUDIT.exists()


def test_audit_mentionne_cloture():
    content = _audit()
    assert "Clôture" in content or "clôture" in content or "terminé" in content


def test_audit_mentionne_nullable_contract_001():
    assert "NULLABLE-CONTRACT-001" in _audit()


def test_audit_mentionne_nullable_contract_002():
    assert "NULLABLE-CONTRACT-002" in _audit()


def test_audit_mentionne_nullable_contract_003():
    assert "NULLABLE-CONTRACT-003" in _audit()


def test_audit_mentionne_nullable_doc_fix_001():
    assert "NULLABLE-DOC-FIX-001" in _audit()


def test_audit_mentionne_adr_013():
    assert "ADR-013" in _audit()


def test_audit_mentionne_nullable_par_defaut():
    content = _audit()
    assert "nullable par défaut" in content or "nullable" in content


def test_audit_mentionne_required_prioritaire():
    content = _audit()
    assert "required" in content and ("prioritaire" in content or "gagne" in content)


def test_audit_mentionne_fields():
    assert "fields[]" in _audit()


def test_audit_mentionne_pivot_fields():
    content = _audit()
    assert "pivot.fields[]" in content or "pivot.fields" in content


def test_audit_ne_dit_pas_schema_modifie():
    content = _audit()
    assert "schéma JSON modifié" not in content
    assert "field.schema.json modifié" not in content


def test_audit_ne_dit_pas_pypi_publie():
    content = _audit()
    assert "PyPI publié" not in content
    assert "forge-mvc publié" not in content
