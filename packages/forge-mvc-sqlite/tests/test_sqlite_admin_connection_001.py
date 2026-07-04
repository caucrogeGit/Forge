"""SQLITE-ADMIN-CONNECTION-001 — SQLite n'a pas de connexion admin (ADR-054).

Le backend SQLite est sans serveur (requires_provisioning=False) : la CLI ne
l'emprunte jamais, et get_admin_connection lève une erreur explicite.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_sqlite")
from forge_mvc_sqlite.backend import SQLiteBackend  # noqa: E402


def test_pas_de_provisioning() -> None:
    assert SQLiteBackend().requires_provisioning is False


def test_get_admin_connection_leve() -> None:
    with pytest.raises(RuntimeError, match="sans serveur"):
        SQLiteBackend().get_admin_connection()
