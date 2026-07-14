"""Tests meta — PIVOT-ADVANCED-002 : UX et modèle d'usage Pivot advanced.

Vérifie que le rapport de décision UX est présent, cohérent et reflète
la décision d'un écran relationnel dédié.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = [pytest.mark.meta, pytest.mark.docs]

RAPPORT = Path("docs/history/audits/pivot-advanced-ux-model-002.md")


def _text() -> str:
    return RAPPORT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_rapport_existe():
    assert RAPPORT.exists()


# ── Ticket de référence ───────────────────────────────────────────────────────


def test_rapport_mentionne_pivot_advanced_002():
    assert "PIVOT-ADVANCED-002" in _text()


# ── Éléments du contrat pivot ─────────────────────────────────────────────────


def test_rapport_mentionne_pivot_fields():
    assert "pivot.fields[]" in _text() or "pivot.fields" in _text()


def test_rapport_mentionne_many_to_many():
    assert "many_to_many" in _text()


def test_rapport_mentionne_make_crud():
    assert "make:crud" in _text()


def test_rapport_dit_make_crud_reste_neutre():
    text = _text()
    assert "neutre" in text.lower() or "reste simple" in text.lower() or "ne génère" in text.lower()


# ── UX retenue ────────────────────────────────────────────────────────────────


def test_rapport_mentionne_ecran_relationnel_dedie():
    text = _text()
    assert "écran relationnel dédié" in text or "écran dédié" in text or "écran relationnel" in text


def test_rapport_mentionne_sous_crud_relationnel():
    text = _text()
    assert "sous-CRUD" in text or "sous-crud" in text.lower()


def test_rapport_mentionne_commande_ou_generateur_dedie():
    text = _text()
    assert "commande" in text.lower() and ("dédié" in text or "générateur" in text.lower())


def test_rapport_mentionne_pivot_advanced_service():
    assert "PivotAdvancedService" in _text()


# ── Actions UX minimales ──────────────────────────────────────────────────────


def test_rapport_mentionne_ajouter_association():
    text = _text()
    assert "ajouter" in text.lower() and "association" in text.lower()


def test_rapport_mentionne_modifier_attributs_pivot():
    text = _text()
    assert "modifier" in text.lower() and ("attribut" in text.lower() or "pivot" in text.lower())


def test_rapport_mentionne_supprimer_association():
    text = _text()
    assert "supprimer" in text.lower() and "association" in text.lower()


# ── Tickets futurs ────────────────────────────────────────────────────────────


def test_rapport_propose_pivot_advanced_003():
    assert "PIVOT-ADVANCED-003" in _text()


def test_rapport_propose_pivot_advanced_close_001():
    assert "PIVOT-ADVANCED-CLOSE-001" in _text()


# ── Absence d'implémentation ──────────────────────────────────────────────────


def test_rapport_ne_dit_pas_ux_implementee():
    text = _text()
    assert "UX implémentée" not in text
    assert "écran implémenté" not in text.lower()


def test_rapport_ne_dit_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
