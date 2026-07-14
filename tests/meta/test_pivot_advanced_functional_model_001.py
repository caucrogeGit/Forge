"""Tests meta — PIVOT-ADVANCED-001 : modèle fonctionnel pivot advanced.

Vérifie que le rapport de décision est présent, cohérent et reflète
la décision de cadrage fonctionnel du pivot advanced.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

RAPPORT = Path("docs/history/audits/pivot-advanced-functional-model-001.md")


def _text() -> str:
    return RAPPORT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_rapport_existe():
    assert RAPPORT.exists()


# ── Ticket de référence ───────────────────────────────────────────────────────


def test_rapport_mentionne_pivot_advanced_001():
    assert "PIVOT-ADVANCED-001" in _text()


# ── Éléments du contrat ───────────────────────────────────────────────────────


def test_rapport_mentionne_pivot_fields():
    assert "pivot.fields[]" in _text() or "pivot.fields" in _text()


def test_rapport_mentionne_many_to_many():
    assert "many_to_many" in _text()


def test_rapport_mentionne_make_crud():
    assert "make:crud" in _text()


def test_rapport_dit_make_crud_reste_simple():
    text = _text()
    assert "neutre" in text.lower() or "reste simple" in text.lower() or "ne lit pas" in text.lower()


# ── Modèle fonctionnel ────────────────────────────────────────────────────────


def test_rapport_mentionne_sous_crud_relationnel():
    text = _text()
    assert "sous-CRUD" in text or "sous-crud" in text.lower() or "sous-CRUD relationnel" in text


def test_rapport_mentionne_service_pivot_advanced():
    text = _text()
    assert "PivotAdvancedService" in text or "service pivot advanced" in text.lower()


def test_rapport_mentionne_commande_ou_generateur_dedie():
    text = _text()
    assert "commande" in text.lower() and ("dédié" in text or "générateur" in text.lower())


# ── Contraintes ───────────────────────────────────────────────────────────────


def test_rapport_mentionne_required():
    assert "required" in _text()


def test_rapport_mentionne_nullable():
    assert "nullable" in _text()


def test_rapport_mentionne_unique_pair():
    assert "unique_pair" in _text()


def test_rapport_mentionne_id_technique():
    text = _text()
    assert "id technique" in text.lower() or "pivot.id" in text or "id` technique" in text


# ── Tickets futurs ────────────────────────────────────────────────────────────


def test_rapport_propose_pivot_advanced_002():
    assert "PIVOT-ADVANCED-002" in _text()


def test_rapport_propose_pivot_advanced_close_001():
    assert "PIVOT-ADVANCED-CLOSE-001" in _text()


# ── Absence d'implémentation ──────────────────────────────────────────────────


def test_rapport_ne_dit_pas_service_implemente():
    text = _text()
    assert "service implémenté" not in text.lower()
    assert "PivotAdvancedService implémenté" not in text


def test_rapport_ne_dit_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
