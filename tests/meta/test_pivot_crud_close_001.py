"""Tests meta — PIVOT-CRUD-CLOSE-001 : clôture du bloc CRUD pivot.fields[].

Vérifie que le rapport d'audit est présent et cohérent avec l'état final :
- les tickets PIVOT-CRUD-001 et PIVOT-CRUD-002 sont mentionnés ;
- la section de clôture est présente ;
- l'état final est documenté (CRUD simple, garde-fou, non-implémentation avancée) ;
- aucune publication PyPI ni tag n'ont été effectués.
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


# ── Tickets mentionnés ────────────────────────────────────────────────────────


def test_rapport_mentionne_pivot_crud_001():
    assert "PIVOT-CRUD-001" in _text()


def test_rapport_mentionne_pivot_crud_002():
    assert "PIVOT-CRUD-002" in _text()


def test_rapport_mentionne_pivot_crud_close_001():
    assert "PIVOT-CRUD-CLOSE-001" in _text()


# ── Contenu minimal ────────────────────────────────────────────────────────────


def test_rapport_mentionne_pivot_fields():
    assert "pivot.fields" in _text() or "pivot.fields[]" in _text()


def test_rapport_mentionne_make_crud():
    assert "make:crud" in _text()


def test_rapport_mentionne_crud_simple():
    text = _text()
    assert "CRUD simple" in text or "synchronise uniquement" in text


def test_rapport_mentionne_required_true():
    text = _text()
    assert "required: true" in text or "required: True" in text


def test_rapport_mentionne_nullable_false():
    text = _text()
    assert "nullable: false" in text or "nullable: False" in text


# ── CRUD pivot avancé non implémenté ──────────────────────────────────────────


def test_rapport_dit_crud_pivot_non_implemente():
    text = _text()
    assert "aucun CRUD pivot avancé" in text or "non implémenté" in text


# ── Section de clôture ────────────────────────────────────────────────────────


def test_rapport_contient_section_cloture():
    text = _text()
    assert "Clôture" in text or "cloture" in text.lower()


def test_rapport_statut_termine():
    text = _text()
    assert "terminé" in text.lower()


# ── Absence de publication ─────────────────────────────────────────────────────


def test_rapport_ne_mentionne_pas_pypi_publie():
    text = _text()
    assert "PyPI publié" not in text
    assert "publié sur PyPI" not in text
    assert "forge-mvc publié" not in text


def test_rapport_ne_mentionne_pas_tag_cree():
    text = _text()
    assert "tag créé" not in text
    assert "tag publié" not in text
