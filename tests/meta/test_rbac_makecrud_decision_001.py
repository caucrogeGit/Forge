"""Tests meta — RBAC-CONTRACT-004 : décision d'intégration RBAC dans make:crud.

Vérifie que le rapport de décision est présent, cohérent et reflète
la décision de non-branchement de make:crud au contrat mvc/security/rbac.json.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

RAPPORT = Path("docs/history/audits/rbac-makecrud-integration-decision-001.md")


def _text() -> str:
    return RAPPORT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_rapport_existe():
    assert RAPPORT.exists()


# ── Contenu ───────────────────────────────────────────────────────────────────


def test_rapport_mentionne_make_crud():
    text = _text()
    assert "make:crud" in text or "make_crud" in text


def test_rapport_mentionne_mvc_security_rbac_json():
    assert "mvc/security/rbac.json" in _text()


def test_rapport_mentionne_rbac_validate():
    assert "rbac:validate" in _text()


def test_rapport_mentionne_option_a():
    assert "Option A" in _text()


def test_rapport_mentionne_option_b():
    assert "Option B" in _text()


def test_rapport_mentionne_option_c():
    assert "Option C" in _text()


def test_rapport_mentionne_option_d():
    assert "Option D" in _text()


def test_rapport_mentionne_risque_couplage():
    text = _text()
    assert "couplage" in text.lower()


def test_rapport_dit_runtime_non_branche():
    text = _text()
    assert "non branché" in text.lower() or "pas encore branché" in text or "NON" in text


# ── Décision correcte ─────────────────────────────────────────────────────────


def test_rapport_decision_option_a():
    text = _text()
    assert "Option A retenue" in text or "ne pas brancher" in text.lower()


def test_rapport_ne_dit_pas_make_crud_modifie():
    text = _text()
    assert "make:crud modifié" not in text
    assert "make_crud modifié" not in text


# ── Absence de publication ─────────────────────────────────────────────────────


def test_rapport_ne_mentionne_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
