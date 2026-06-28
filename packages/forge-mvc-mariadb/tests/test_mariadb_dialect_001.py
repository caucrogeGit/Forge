"""MARIADB-DIALECT-001 — mapping des types Forge vers MariaDB (ADR-054)."""
from __future__ import annotations

import pytest

pytest.importorskip("forge_mvc_mariadb")
from forge_mvc_mariadb.dialect import MariaDBDialect  # noqa: E402

D = MariaDBDialect()


def test_identity_type() -> None:
    assert D.identity_type() == "BIGINT UNSIGNED"


def test_string_et_decimal() -> None:
    assert D.string_type(120) == "VARCHAR(120)"
    assert D.decimal_type(10, 2) == "DECIMAL(10,2)"


@pytest.mark.parametrize(
    "forge_type, expected",
    [
        ("text", "TEXT"),
        ("integer", "INT"),
        ("big_integer", "BIGINT"),
        ("float", "DOUBLE"),
        ("boolean", "BOOLEAN"),
        ("date", "DATE"),
        ("datetime", "DATETIME"),
        ("email", "VARCHAR(255)"),
        ("password", "VARCHAR(255)"),
        ("slug", "VARCHAR(180)"),
        ("json", "LONGTEXT"),
    ],
)
def test_simple_types(forge_type: str, expected: str) -> None:
    assert D.simple_type(forge_type) == expected


def test_add_columns_sql_un_seul_alter() -> None:
    sql = D.add_columns_sql(
        "contact",
        [("Email", "VARCHAR(120) NULL"), ("Tel", "VARCHAR(20) NULL")],
    )
    assert sql == (
        "ALTER TABLE `contact`\n"
        "    ADD COLUMN `Email` VARCHAR(120) NULL,\n"
        "    ADD COLUMN `Tel` VARCHAR(20) NULL;\n"
    )


def test_quote_identifier_backticks() -> None:
    assert D.quote_identifier("contact") == "`contact`"
