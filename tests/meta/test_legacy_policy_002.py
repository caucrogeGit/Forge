"""Tests meta — LEGACY-POLICY-002 : politique de dépréciation du format legacy.

Vérifie que le document de décision ADR-012 existe et couvre les points requis.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ADR = Path("docs/adr/012-legacy-format-deprecation-policy.md")


def _adr() -> str:
    return ADR.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_adr_existe():
    assert ADR.exists()


# ── Contenu obligatoire ────────────────────────────────────────────────────────


def test_adr_mentionne_format_version():
    assert "format_version" in _adr()


def test_adr_mentionne_schema_version():
    assert "schema_version" in _adr()


def test_adr_mentionne_format_canonique_recommande():
    content = _adr()
    assert "format officiel" in content or "recommandé" in content


def test_adr_mentionne_legacy_deprecie():
    content = _adr()
    assert "déprécié" in content or "Déprécié" in content


def test_adr_mentionne_legacy_supporte_temporairement():
    content = _adr()
    assert "temporairement" in content or "temporaire" in content


def test_adr_mentionne_starters_sans_legacy():
    content = _adr()
    assert "starter" in content.lower()
    assert "canonique" in content or "canonical" in content


def test_adr_mentionne_conditions_avant_suppression():
    content = _adr()
    assert "Conditions avant suppression" in content or "conditions" in content.lower()


def test_adr_ne_dit_pas_legacy_supprime():
    content = _adr()
    assert "legacy supprimé" not in content
    assert "support legacy supprimé" not in content


def test_adr_ne_dit_pas_pypi_publie():
    content = _adr()
    assert "PyPI publié" not in content
    assert "forge-mvc publié" not in content


# ── Structure ──────────────────────────────────────────────────────────────────


def test_adr_mentionne_statut_accepte():
    assert "Acceptée" in _adr() or "Accepté" in _adr()


def test_adr_mentionne_legacy_policy_001():
    assert "LEGACY-POLICY-001" in _adr()


def test_adr_mentionne_legacy_remove_001():
    assert "LEGACY-REMOVE-001" in _adr()


def test_adr_mentionne_consequences():
    assert "Conséquences" in _adr() or "conséquences" in _adr()


# ── Audit mis à jour ───────────────────────────────────────────────────────────

AUDIT = Path("docs/history/audits/legacy-support-core-audit-001.md")


def test_audit_mentionne_adr_012():
    content = AUDIT.read_text(encoding="utf-8")
    assert "ADR-012" in content


def test_audit_mentionne_decision_post_audit():
    content = AUDIT.read_text(encoding="utf-8")
    assert "Décision post-audit" in content or "décision post-audit" in content


def test_audit_mentionne_legacy_policy_002_livre():
    content = AUDIT.read_text(encoding="utf-8")
    assert "LEGACY-POLICY-002" in content
    assert "Livré" in content or "livré" in content
