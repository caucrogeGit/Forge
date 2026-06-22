"""Tests meta — STARTERS-LEGACY-001 : audit des starters en format legacy.

Vérifie que le document d'audit existe et couvre les points requis :
présence de la matrice, détection du format legacy, risques identifiés.
"""

from __future__ import annotations

import pathlib

import pytest

pytestmark = pytest.mark.meta

AUDIT = pathlib.Path("docs/history/audits/starters-legacy-audit-json-schema-001.md")
STARTERS_DIR = pathlib.Path("cli/starters/data")


def _r() -> str:
    return AUDIT.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Existence
# ---------------------------------------------------------------------------


def test_audit_existe():
    assert AUDIT.exists()


# ---------------------------------------------------------------------------
# Format legacy documenté
# ---------------------------------------------------------------------------


def test_mentionne_format_version():
    assert "format_version" in _r()


def test_mentionne_schema_version():
    assert "schema_version" in _r()


# ---------------------------------------------------------------------------
# Commandes clés mentionnées
# ---------------------------------------------------------------------------


def test_mentionne_entity_validate():
    assert "entity:validate" in _r()


def test_mentionne_starter_build():
    r = _r()
    assert "starter:build" in r or "build:model" in r


# ---------------------------------------------------------------------------
# Matrice d'audit présente
# ---------------------------------------------------------------------------


def test_mentionne_matrice():
    r = _r()
    assert "matrice" in r.lower() or "Matrice" in r


def test_mentionne_les_5_starters_avec_entites():
    r = _r()
    assert "contact-simple" in r
    assert "carnet-contacts" in r
    assert "utilisateurs-auth" in r
    assert "suivi-comportement-eleves" in r
    assert "communes-sejours" in r


# ---------------------------------------------------------------------------
# Risques documentés
# ---------------------------------------------------------------------------


def test_mentionne_risques():
    r = _r()
    assert "Risques" in r or "risques" in r


# ---------------------------------------------------------------------------
# Migration non marquée livrée dans ce ticket
# ---------------------------------------------------------------------------


def test_migration_starters_pas_marquee_livree():
    r = _r()
    lower = r.lower()
    if "migration" in lower and "livr" in lower:
        migration_idx = lower.index("migration")
        window = lower[migration_idx:migration_idx + 120]
        assert "livré" not in window and "livrée" not in window, (
            "La migration des starters ne doit pas être marquée livrée dans ce ticket d'audit."
        )
