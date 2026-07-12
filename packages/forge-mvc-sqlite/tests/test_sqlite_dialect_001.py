"""SQLITE-DIALECT-001 — mapping des types Forge vers SQLite (ADR-054).

Vérifie le dialecte SQLite isolé, puis de bout en bout : le normaliseur du
cœur produit bien des types SQLite quand le backend actif est SQLite.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_sqlite")
from forge_mvc_sqlite.dialect import SQLiteDialect  # noqa: E402

D = SQLiteDialect()


def test_identity_et_string_et_decimal() -> None:
    assert D.identity_type() == "INTEGER"
    assert D.string_type(120) == "TEXT"  # SQLite ignore la longueur
    assert D.decimal_type(10, 2) == "NUMERIC"


def test_foreign_key_checks_ddl() -> None:
    # ADR-077 : PRAGMA SQLite (sans effet dans une transaction ouverte).
    assert D.foreign_key_checks_ddl(enabled=False) == ["PRAGMA foreign_keys = OFF"]
    assert D.foreign_key_checks_ddl(enabled=True) == ["PRAGMA foreign_keys = ON"]


@pytest.mark.parametrize(
    "forge_type, expected",
    [
        ("text", "TEXT"),
        ("integer", "INTEGER"),
        ("big_integer", "INTEGER"),
        ("float", "REAL"),
        ("boolean", "INTEGER"),
        ("date", "TEXT"),
        ("datetime", "TEXT"),
        ("json", "TEXT"),
    ],
)
def test_simple_types(forge_type: str, expected: str) -> None:
    assert D.simple_type(forge_type) == expected


def test_normaliseur_produit_des_types_sqlite(monkeypatch: pytest.MonkeyPatch) -> None:
    """Bout en bout : sous DB_BACKEND=sqlite, le normaliseur émet des types SQLite."""
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    from core.database import backend as backend_module
    from forge_mvc_entities.canonical_model_normalizer import (
        normalize_canonical_entity_for_model_build,
    )

    backend_module.reset_backend()
    try:
        entity = {
            "name": "Contact",
            "table": "contact",
            "fields": [
                {"name": "nom", "type": "string", "max_length": 120},
                {"name": "age", "type": "integer"},
            ],
            "options": {"timestamps": True},
        }
        result = normalize_canonical_entity_for_model_build(entity)
        by_name = {f["name"]: f for f in result["fields"]}
        assert by_name["id"]["sql_type"] == "INTEGER"
        assert by_name["nom"]["sql_type"] == "TEXT"
        assert by_name["age"]["sql_type"] == "INTEGER"
        assert by_name["created_at"]["sql_type"] == "TEXT"
    finally:
        backend_module.reset_backend()


def test_add_columns_sql_un_alter_par_colonne() -> None:
    sql = D.add_columns_sql("contact", [("Email", "TEXT"), ("Age", "INTEGER")])
    assert sql == (
        'ALTER TABLE "contact" ADD COLUMN "Email" TEXT;\n'
        'ALTER TABLE "contact" ADD COLUMN "Age" INTEGER;\n'
    )


def test_add_columns_sql_executable() -> None:
    import sqlite3

    sql = D.add_columns_sql("contact", [("Email", "TEXT"), ("Age", "INTEGER")])
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("CREATE TABLE contact (Id INTEGER PRIMARY KEY AUTOINCREMENT)")
        conn.executescript(sql)
        cols = {row[1] for row in conn.execute("PRAGMA table_info(contact)")}
        assert {"Id", "Email", "Age"} <= cols
    finally:
        conn.close()
