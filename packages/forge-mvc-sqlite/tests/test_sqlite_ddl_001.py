"""SQLITE-DDL-001 — la DDL générée par Forge est valide et exécutable en SQLite.

Bout en bout : sous DB_BACKEND=sqlite, build_entity_sql produit un CREATE TABLE
SQLite idiomatique (INTEGER PRIMARY KEY AUTOINCREMENT, pas d'ENGINE, UNIQUE(...))
que sqlite3 (stdlib) exécute réellement.

Depuis DB-DIALECT-VALIDATION-001, la validation d'entité est dialecte-aware :
les types SQLite de date/heure/booléen (datetime/date -> TEXT, boolean ->
INTEGER) sont acceptés. Ce test inclut donc des timestamps et un booléen.
"""
from __future__ import annotations

import sqlite3

import pytest

pytest.importorskip("forge_mvc_sqlite")


def _build_create_table() -> str:
    from forge_mvc_entities.canonical_model_normalizer import (
        normalize_canonical_entity_for_model_build,
    )
    from forge_mvc_entities.make_entity import build_entity_sql

    entity = {
        "name": "Contact",
        "table": "contact",
        "fields": [
            {"name": "nom", "type": "string", "max_length": 120, "required": True, "unique": True},
            {"name": "age", "type": "integer"},
            {"name": "actif", "type": "boolean"},
        ],
        "options": {"timestamps": True},
    }
    return build_entity_sql(normalize_canonical_entity_for_model_build(entity))


def test_ddl_sqlite_idiomatique(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    from core.database import backend as backend_module

    backend_module.reset_backend()
    try:
        sql = _build_create_table()
        assert "INTEGER PRIMARY KEY AUTOINCREMENT" in sql
        assert "ENGINE=" not in sql
        assert "AUTO_INCREMENT" not in sql  # mot-clé MariaDB absent
        assert "UNIQUE KEY" not in sql      # forme MariaDB absente
        assert "Nom TEXT NOT NULL UNIQUE" in sql  # unicité portée par la colonne
    finally:
        backend_module.reset_backend()


def test_ddl_sexecute_dans_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    from core.database import backend as backend_module

    backend_module.reset_backend()
    try:
        sql = _build_create_table()
    finally:
        backend_module.reset_backend()

    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(sql)  # lève si la DDL est invalide
        conn.execute(
            "INSERT INTO contact (Nom, Age, Actif, CreatedAt, UpdatedAt) "
            "VALUES (?, ?, ?, ?, ?)",
            ("Ada", 36, 1, "2026-01-01 00:00:00", "2026-01-01 00:00:00"),
        )
        cur = conn.execute("SELECT Id, Nom, Age, Actif FROM contact")
        assert cur.fetchone() == (1, "Ada", 36, 1)
    finally:
        conn.close()
