"""Tests meta — PIVOT-CRUD-001 : audit du comportement CRUD des attributs de pivot.

Vérifie que le rapport d'audit est présent et cohérent avec les décisions prises :
- pivot.fields[] est validé et génère du SQL ;
- make:crud n'expose pas les attributs pivot dans le CRUD généré ;
- les options A, B, C, D sont documentées ;
- le CRUD pivot avancé n'est pas déclaré comme implémenté ;
- les tickets futurs sont proposés.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

RAPPORT = Path("docs/history/audits/pivot-crud-audit-001.md")


def _text() -> str:
    return RAPPORT.read_text(encoding="utf-8")


# ── Existence ──────────────────────────────────────────────────────────────────


def test_rapport_existe():
    assert RAPPORT.exists()


# ── Contenu minimal ────────────────────────────────────────────────────────────


def test_rapport_mentionne_pivot_fields():
    assert "pivot.fields" in _text() or "pivot.fields[]" in _text()


def test_rapport_mentionne_many_to_many():
    text = _text()
    assert "many_to_many" in text or "many-to-many" in text


def test_rapport_mentionne_make_crud():
    text = _text()
    assert "make:crud" in text


def test_rapport_mentionne_sql_pivot():
    text = _text()
    assert "SQL" in text
    assert "pivot" in text.lower()


# ── Options étudiées ──────────────────────────────────────────────────────────


def test_rapport_mentionne_option_a():
    assert "Option A" in _text()


def test_rapport_mentionne_option_b():
    assert "Option B" in _text()


def test_rapport_mentionne_option_c():
    assert "Option C" in _text()


def test_rapport_mentionne_option_d():
    assert "Option D" in _text()


# ── Risques ───────────────────────────────────────────────────────────────────


def test_rapport_mentionne_risque_complexite():
    text = _text()
    assert "complexit" in text.lower() or "complex" in text.lower()


def test_rapport_mentionne_risque_regression():
    text = _text()
    assert "régression" in text.lower() or "regression" in text.lower()


def test_rapport_mentionne_risque_integrite():
    text = _text()
    assert "NOT NULL" in text or "intégrit" in text.lower()


# ── Décision ──────────────────────────────────────────────────────────────────


def test_rapport_dit_option_a_retenue():
    text = _text()
    assert "Option A retenue" in text or "ne pas intégrer" in text.lower()


# ── CRUD pivot avancé non implémenté ──────────────────────────────────────────


def test_rapport_ne_dit_pas_crud_pivot_implemente():
    text = _text()
    # La mention dans le tableau "NON" est attendue ; on vérifie qu'il n'y a pas
    # d'affirmation positive d'implémentation.
    assert "CRUD pivot avancé implémenté : OUI" not in text
    assert "édition pivot implémentée" not in text
    assert "pivot.fields[] édités dans make:crud" not in text


def test_rapport_ne_dit_pas_formulaires_pivot_generes():
    text = _text()
    assert "formulaires pivot générés" not in text


# ── Tickets futurs ────────────────────────────────────────────────────────────


def test_rapport_propose_pivot_crud_002():
    assert "PIVOT-CRUD-002" in _text()


# ── Absence de publication ─────────────────────────────────────────────────────


def test_rapport_ne_mentionne_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
    assert "forge-mvc publié" not in text
