"""MSSQL-DIALECT-001 — traits SQL Microsoft SQL Server (ADR-054)."""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mssql")
from forge_mvc_mssql.dialect import MSSQLDialect  # noqa: E402

D = MSSQLDialect()


def test_identity_storage_type() -> None:
    # FK-IDENTITY-STORAGE-TYPE-001 : IDENTITY est une propriété de colonne, et
    # SQL Server n'en admet qu'une par table, déjà prise par la clé primaire.
    # Une clé étrangère typée IDENTITY rendrait le CREATE TABLE invalide.
    assert D.identity_storage_type() == "BIGINT"
    assert "IDENTITY" not in D.identity_storage_type()


def test_types() -> None:
    assert D.identity_type() == "BIGINT IDENTITY(1,1)"
    assert D.string_type(120) == "NVARCHAR(120)"
    assert D.decimal_type(10, 2) == "DECIMAL(10,2)"
    assert D.simple_type("datetime") == "DATETIME2"
    assert D.simple_type("boolean") == "BIT"
    assert D.simple_type("text") == "NVARCHAR(MAX)"


@pytest.mark.parametrize(
    "sql_type, family",
    [
        ("BIGINT IDENTITY(1,1)", "int"),
        ("INT", "int"),
        ("BIGINT", "int"),
        ("NVARCHAR(120)", "str"),
        ("NVARCHAR(MAX)", "str"),
        ("BIT", "bool"),
        ("DATE", "date"),
        ("DATETIME2", "datetime"),
        ("DECIMAL(10,2)", "float"),
        ("FLOAT", "float"),
    ],
)
def test_sql_families(sql_type: str, family: str) -> None:
    assert family in D.sql_families(sql_type)


def test_ddl_primitives() -> None:
    assert D.auto_increment_column_ddl("id", "BIGINT IDENTITY(1,1)") == "id BIGINT IDENTITY(1,1)"
    assert D.emits_separate_primary_key() is True
    assert D.unique_is_column_constraint() is True
    assert D.table_suffix() == ""
    assert D.quote_identifier("contact") == "[contact]"
    assert D.inline_indexes() is False
    assert D.named_unique("uq_x", ["a", "b"]) == "CONSTRAINT uq_x UNIQUE (a, b)"


def test_create_table_opening_garde() -> None:
    assert D.create_table_opening("contact") == (
        "IF OBJECT_ID(N'contact', N'U') IS NULL\nCREATE TABLE contact"
    )


def test_create_index_garde() -> None:
    sql = D.create_index_sql("contact", "idx_c", "email")
    assert "IF NOT EXISTS (SELECT 1 FROM sys.indexes" in sql
    assert "CREATE INDEX idx_c ON contact (email);" in sql


def test_add_columns_sql_un_alter() -> None:
    sql = D.add_columns_sql("contact", [("email", "NVARCHAR(120)"), ("age", "INT")])
    assert sql == (
        "ALTER TABLE [contact]\n"
        "    ADD [email] NVARCHAR(120),\n"
        "        [age] INT;\n"
    )


def test_forge_migrations_ddl_identity_et_garde() -> None:
    ddl = D.forge_migrations_ddl()
    assert "IF OBJECT_ID(N'forge_migrations', N'U') IS NULL" in ddl
    assert "id BIGINT IDENTITY(1,1) PRIMARY KEY" in ddl
    assert "UNIQUE (version)" in ddl


def test_foreign_key_checks_ddl_is_empty() -> None:
    # ADR-077 : SQL Server n'a pas de levier FK de session ; liste vide.
    assert D.foreign_key_checks_ddl(enabled=False) == []
    assert D.foreign_key_checks_ddl(enabled=True) == []


def test_ddl_auth_adr_084() -> None:
    # ADR-084 : traits DDL du socle Auth/User.
    assert D.auto_increment_primary_key_ddl("id", "INT") == "id INT IDENTITY(1,1) PRIMARY KEY"
    assert D.char_type(64) == "CHAR(64)"
    assert D.boolean_default_literal(True) == "1"
    assert D.boolean_default_literal(False) == "0"
    # Pas d'ON UPDATE déclaratif en T-SQL ; SYSUTCDATETIME() comme forge_migrations.
    assert D.timestamp_default_clause(on_update=False) == "DEFAULT SYSUTCDATETIME()"
    assert D.timestamp_default_clause(on_update=True) == "DEFAULT SYSUTCDATETIME()"
    assert D.collated_table_suffix() == ""


def test_add_foreign_key_sql_adr_084() -> None:
    # ADR-084 : ADD sans mot-clé COLUMN (T-SQL), RESTRICT traduit en NO ACTION.
    statements = D.add_foreign_key_sql(
        table="classe",
        column="annee_scolaire_id",
        sql_type="BIGINT",
        nullable=True,
        ref_table="annee_scolaire",
        ref_column="id",
        constraint_name="fk_classe_annee_scolaire_id",
        on_delete="RESTRICT",
        on_update="RESTRICT",
        index_name="idx_classe_annee_scolaire_id",
        add_column=True,
    )
    assert statements[0] == "ALTER TABLE classe\n    ADD annee_scolaire_id BIGINT NULL;"
    assert "ADD COLUMN" not in statements[0]
    assert "ON DELETE NO ACTION" in statements[1]
    assert "ON UPDATE NO ACTION" in statements[1]
    assert "RESTRICT" not in statements[1]
    assert "CREATE INDEX idx_classe_annee_scolaire_id ON classe (annee_scolaire_id);" in statements[2]
