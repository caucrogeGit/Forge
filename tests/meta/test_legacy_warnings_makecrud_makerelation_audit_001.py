"""Tests meta — LEGACY-WARNINGS-003 : audit warnings legacy make:crud et make:relation."""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

AUDIT = Path("docs/history/audits/legacy-warnings-makecrud-makerelation-audit-001.md")


def _audit() -> str:
    return AUDIT.read_text(encoding="utf-8")


def test_audit_existe():
    assert AUDIT.exists()


def test_audit_mentionne_make_crud():
    assert "make:crud" in _audit()


def test_audit_mentionne_make_relation():
    assert "make:relation" in _audit()


def test_audit_mentionne_format_version():
    assert "format_version" in _audit()


def test_audit_mentionne_schema_version():
    assert "schema_version" in _audit()


def test_audit_mentionne_legacy():
    content = _audit()
    assert "legacy" in content or "Legacy" in content


def test_audit_mentionne_warning():
    content = _audit()
    assert "warning" in content or "Warning" in content or "WARN" in content


def test_audit_mentionne_risques_bruit():
    content = _audit()
    assert "bruit" in content or "risque" in content


def test_audit_propose_legacy_warnings_004():
    assert "LEGACY-WARNINGS-004" in _audit()


def test_audit_ne_dit_pas_warnings_runtime_ajoutes():
    content = _audit()
    assert "warning ajouté" not in content
    assert "warnings ajoutés" not in content
    assert "warning runtime implémenté" not in content


def test_audit_mentionne_options():
    content = _audit()
    assert "Option A" in content and "Option B" in content


def test_audit_mentionne_recommandation():
    content = _audit()
    assert "Recommandation" in content or "recommandation" in content
