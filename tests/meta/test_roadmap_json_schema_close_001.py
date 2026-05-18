"""Tests meta — ENTITY-CONTRACT-023 : clôture de la roadmap Contrats JSON Schema.

Vérifie que la roadmap autonome est bien marquée terminée et que ses
sections obligatoires sont présentes.
"""

from __future__ import annotations

import pathlib

import pytest

pytestmark = pytest.mark.meta

ROADMAP = pathlib.Path("docs/roadmap/roadmap-forge-contrats-json-schema.md")


def _r() -> str:
    return ROADMAP.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


def test_roadmap_existe():
    assert ROADMAP.exists()


# ---------------------------------------------------------------------------
# Ticket de clôture présent et marqué livré
# ---------------------------------------------------------------------------


def test_mentionne_entity_contract_023():
    assert "ENTITY-CONTRACT-023" in _r()


def test_roadmap_terminee():
    r = _r()
    assert "terminée" in r or "clôturée" in r


# ---------------------------------------------------------------------------
# Commandes clés mentionnées
# ---------------------------------------------------------------------------


def test_mentionne_schema_list():
    assert "schema:list" in _r()


def test_mentionne_schema_doctor():
    assert "schema:doctor" in _r()


def test_mentionne_entity_validate():
    assert "entity:validate" in _r()


# ---------------------------------------------------------------------------
# Limites restantes documentées
# ---------------------------------------------------------------------------


def test_mentionne_limites_restantes():
    r = _r()
    assert "Limites restantes" in r or "limites restantes" in r


def test_mentionne_pypi_differe():
    r = _r()
    assert "PyPI" in r and ("différé" in r or "différée" in r or "blocage" in r)


def test_mentionne_starters_legacy():
    r = _r()
    assert "starters" in r.lower() and ("legacy" in r.lower() or "migr" in r.lower())


# ---------------------------------------------------------------------------
# Starters non marqués livrés dans ce ticket
# ---------------------------------------------------------------------------


def test_migration_starters_pas_marquee_livree():
    r = _r()
    assert "migration des starters" not in r.lower() or (
        "migration des starters" in r.lower()
        and "livré" not in r[r.lower().index("migration des starters"):
                              r.lower().index("migration des starters") + 80]
    )
