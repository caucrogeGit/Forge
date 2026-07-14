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


def test_foreign_key_checks_ddl() -> None:
    # ADR-077 : levier de session MariaDB.
    assert D.foreign_key_checks_ddl(enabled=False) == ["SET FOREIGN_KEY_CHECKS = 0"]
    assert D.foreign_key_checks_ddl(enabled=True) == ["SET FOREIGN_KEY_CHECKS = 1"]


def test_ddl_auth_adr_084() -> None:
    # ADR-084 : traits DDL du socle Auth/User.
    assert D.auto_increment_primary_key_ddl("id", "INT") == "id INT AUTO_INCREMENT PRIMARY KEY"
    assert D.char_type(64) == "CHAR(64)"
    assert D.boolean_default_literal(True) == "TRUE"
    assert D.boolean_default_literal(False) == "FALSE"
    assert D.timestamp_default_clause(on_update=False) == "DEFAULT CURRENT_TIMESTAMP"
    assert D.timestamp_default_clause(on_update=True) == (
        "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
    )
    assert D.collated_table_suffix() == (
        " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    )


def test_add_foreign_key_sql_adr_084() -> None:
    # ADR-084 : pose de FK many_to_one, forme historique conservée.
    statements = D.add_foreign_key_sql(
        table="classe",
        column="annee_scolaire_id",
        sql_type="BIGINT UNSIGNED",
        nullable=True,
        ref_table="annee_scolaire",
        ref_column="id",
        constraint_name="fk_classe_annee_scolaire_id",
        on_delete="RESTRICT",
        on_update="RESTRICT",
        index_name="idx_classe_annee_scolaire_id",
        add_column=True,
    )
    assert statements == [
        "ALTER TABLE classe\n    ADD COLUMN annee_scolaire_id BIGINT UNSIGNED NULL;",
        "ALTER TABLE classe\n"
        "    ADD CONSTRAINT fk_classe_annee_scolaire_id\n"
        "    FOREIGN KEY (annee_scolaire_id)\n"
        "    REFERENCES annee_scolaire (id)\n"
        "    ON DELETE RESTRICT\n"
        "    ON UPDATE RESTRICT;",
        "CREATE INDEX idx_classe_annee_scolaire_id ON classe (annee_scolaire_id);",
    ]
