"""Tests meta — NULLABLE-CONTRACT-002 : décision de la politique nullable/required."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

ADR = Path("docs/adr/013-nullable-required-contract-policy.md")
AUDIT = Path("docs/history/audits/nullable-contract-audit-001.md")


def _adr() -> str:
    return ADR.read_text(encoding="utf-8")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_adr_existe():
    assert ADR.exists()


# ── Contenu obligatoire ────────────────────────────────────────────────────────


def test_adr_mentionne_nullable():
    assert "nullable" in _adr()


def test_adr_mentionne_required():
    assert "required" in _adr()


def test_adr_mentionne_fields():
    assert "fields[]" in _adr()


def test_adr_mentionne_pivot_fields():
    content = _adr()
    assert "pivot.fields[]" in content or "pivot.fields" in content


def test_adr_mentionne_null():
    assert "NULL" in _adr()


def test_adr_mentionne_not_null():
    assert "NOT NULL" in _adr()


def test_adr_required_est_prioritaire():
    content = _adr()
    assert "prioritaire" in content or "gagne" in content


def test_adr_nullable_par_defaut():
    content = _adr()
    assert "par défaut" in content or "défaut" in content


def test_adr_mentionne_nullable_contract_003():
    assert "NULLABLE-CONTRACT-003" in _adr()


def test_adr_ne_dit_pas_correction_appliquee():
    content = _adr()
    assert "correction appliquée" not in content
    assert "runtime corrigé" not in content


# ── Audit mis à jour ───────────────────────────────────────────────────────────


def test_audit_mentionne_decision_post_audit():
    content = _audit()
    assert "Décision post-audit" in content or "décision post-audit" in content


def test_audit_mentionne_adr_013():
    assert "ADR-013" in _audit()
