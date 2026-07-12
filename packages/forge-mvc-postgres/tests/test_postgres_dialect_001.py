"""POSTGRES-DIALECT-001 — traits SQL PostgreSQL (ADR-054)."""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_postgres")
from forge_mvc_postgres.dialect import PostgreSQLDialect  # noqa: E402

D = PostgreSQLDialect()


def test_types() -> None:
    assert D.identity_type() == "BIGSERIAL"
    assert D.string_type(120) == "VARCHAR(120)"
    assert D.decimal_type(10, 2) == "NUMERIC(10,2)"
    assert D.simple_type("datetime") == "TIMESTAMP"
    assert D.simple_type("boolean") == "BOOLEAN"
    assert D.simple_type("json") == "JSONB"


@pytest.mark.parametrize(
    "sql_type, family",
    [
        ("BIGSERIAL", "int"),
        ("INTEGER", "int"),
        ("BIGINT", "int"),
        ("VARCHAR(120)", "str"),
        ("TEXT", "str"),
        ("JSONB", "str"),
        ("BOOLEAN", "bool"),
        ("DATE", "date"),
        ("TIMESTAMP", "datetime"),
        ("NUMERIC(10,2)", "float"),
        ("DOUBLE PRECISION", "float"),
    ],
)
def test_sql_families(sql_type: str, family: str) -> None:
    assert family in D.sql_families(sql_type)


def test_ddl_primitives() -> None:
    assert D.auto_increment_column_ddl("id", "BIGSERIAL") == "id BIGSERIAL"
    assert D.emits_separate_primary_key() is True
    assert D.unique_is_column_constraint() is True
    assert D.table_suffix() == ""
    assert D.quote_identifier("contact") == '"contact"'
    assert D.inline_indexes() is False
    assert D.named_unique("uq_x", ["a", "b"]) == "CONSTRAINT uq_x UNIQUE (a, b)"
    assert (
        D.create_index_sql("contact", "idx_c", "email")
        == "CREATE INDEX IF NOT EXISTS idx_c ON contact (email);"
    )


def test_add_columns_sql_un_alter() -> None:
    sql = D.add_columns_sql("contact", [("email", "VARCHAR(120)"), ("age", "INTEGER")])
    assert sql == (
        'ALTER TABLE "contact"\n'
        '    ADD COLUMN "email" VARCHAR(120),\n'
        '    ADD COLUMN "age" INTEGER;\n'
    )


def test_forge_migrations_ddl_bigserial() -> None:
    ddl = D.forge_migrations_ddl()
    assert "id BIGSERIAL PRIMARY KEY" in ddl
    assert "UNIQUE (version)" in ddl


def test_foreign_key_checks_ddl() -> None:
    # ADR-077 : PostgreSQL passe par session_replication_role.
    assert D.foreign_key_checks_ddl(enabled=False) == [
        "SET session_replication_role = replica"
    ]
    assert D.foreign_key_checks_ddl(enabled=True) == [
        "SET session_replication_role = origin"
    ]
