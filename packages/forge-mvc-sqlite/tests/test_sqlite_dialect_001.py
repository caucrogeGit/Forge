"""SQLITE-DIALECT-001 — mapping des types Forge vers SQLite (ADR-054).

Vérifie le dialecte SQLite isolé, puis de bout en bout : le normaliseur du
cœur produit bien des types SQLite quand le backend actif est SQLite.
"""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_sqlite")
from forge_mvc_sqlite.dialect import SQLiteDialect  # noqa: E402

D = SQLiteDialect()


def test_identity_storage_type() -> None:
    # FK-IDENTITY-STORAGE-TYPE-001 : AUTOINCREMENT est une clause portée par la
    # colonne PK ; INTEGER est déjà un type de stockage ordinaire.
    assert D.identity_storage_type() == "INTEGER"


def test_identity_et_string_et_decimal() -> None:
    assert D.identity_type() == "INTEGER"
    assert D.string_type(120) == "TEXT"  # SQLite ignore la longueur
    assert D.decimal_type(10, 2) == "NUMERIC"


def test_foreign_key_checks_ddl() -> None:
    # ADR-077, revu par SQLITE-FOREIGN-KEYS-ON-001 : `PRAGMA foreign_keys` est
    # sans effet dans une transaction ouverte, or c'est là que fixtures:load
    # l'émet. Seul `defer_foreign_keys` y agit.
    assert D.foreign_key_checks_ddl(enabled=False) == ["PRAGMA defer_foreign_keys = ON"]
    assert D.foreign_key_checks_ddl(enabled=True) == ["PRAGMA defer_foreign_keys = OFF"]


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


def test_ddl_auth_adr_084() -> None:
    # ADR-084 : traits DDL du socle Auth/User (affinités SQLite).
    assert D.auto_increment_primary_key_ddl("id", "INTEGER") == "id INTEGER PRIMARY KEY AUTOINCREMENT"
    assert D.char_type(64) == "TEXT"
    assert D.boolean_default_literal(True) == "1"
    assert D.boolean_default_literal(False) == "0"
    # Pas d'ON UPDATE déclaratif en SQLite : clause identique dans les deux cas.
    assert D.timestamp_default_clause(on_update=False) == "DEFAULT CURRENT_TIMESTAMP"
    assert D.timestamp_default_clause(on_update=True) == "DEFAULT CURRENT_TIMESTAMP"
    assert D.collated_table_suffix() == ""


def test_add_foreign_key_sql_inline_references_executable() -> None:
    # ADR-084 : pas d'ADD CONSTRAINT en SQLite ; REFERENCES inline sur ADD COLUMN.
    import sqlite3

    statements = D.add_foreign_key_sql(
        table="classe",
        column="annee_scolaire_id",
        sql_type="INTEGER",
        nullable=True,
        ref_table="annee_scolaire",
        ref_column="id",
        constraint_name="fk_classe_annee_scolaire_id",
        on_delete="RESTRICT",
        on_update="RESTRICT",
        index_name="idx_classe_annee_scolaire_id",
        add_column=True,
    )
    sql = "\n".join(statements)
    assert "ADD CONSTRAINT" not in sql
    assert "REFERENCES annee_scolaire (id)" in sql
    conn = sqlite3.connect(":memory:")
    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("CREATE TABLE annee_scolaire (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        conn.execute("CREATE TABLE classe (id INTEGER PRIMARY KEY AUTOINCREMENT)")
        conn.executescript(sql)
        fks = list(conn.execute("PRAGMA foreign_key_list(classe)"))
        assert any(row[2] == "annee_scolaire" for row in fks)
    finally:
        conn.close()


def test_add_foreign_key_sql_colonne_existante_commentaire_seul() -> None:
    # ADR-084, règle B : colonne déjà déclarée, aucun énoncé inapplicable.
    statements = D.add_foreign_key_sql(
        table="classe",
        column="annee_scolaire_id",
        sql_type="INTEGER",
        nullable=True,
        ref_table="annee_scolaire",
        ref_column="id",
        constraint_name="fk_classe_annee_scolaire_id",
        on_delete="RESTRICT",
        on_update="RESTRICT",
        index_name=None,
        add_column=False,
    )
    assert len(statements) == 1
    assert all(line.startswith("--") for line in statements[0].splitlines())
    assert "ADR-084" in statements[0]
