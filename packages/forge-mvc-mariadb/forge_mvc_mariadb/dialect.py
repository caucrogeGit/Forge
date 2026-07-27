# pyright: strict
# pyright: reportMissingTypeStubs=false
"""
forge_mvc_mariadb.dialect — Traits SQL MariaDB (ADR-054)
========================================================
Mapping des types Forge vers les types de colonne MariaDB. Reproduit à
l'identique le mapping historiquement codé dans le normaliseur du cœur, pour
ne rien changer au SQL généré tant que le backend est MariaDB.
"""
from typing import Any

from core.database.literals import escape_string, render_literal_value

# Types Forge « simples » → type de colonne MariaDB.
# boolean → BOOLEAN (et non TINYINT(1)) : voir la note du normaliseur.
_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INT",
    "big_integer": "BIGINT",
    "float":       "DOUBLE",
    "boolean":     "BOOLEAN",
    "date":        "DATE",
    "datetime":    "DATETIME",
    "email":       "VARCHAR(255)",
    "password":    "VARCHAR(255)",
    "slug":        "VARCHAR(180)",
    "json":        "LONGTEXT",
}

# Préfixes de types SQL MariaDB par famille Python (compatibilité sql/python).
_INTEGER_PREFIXES = ("INT", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT")
_FLOAT_PREFIXES = ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")
_STRING_PREFIXES = ("CHAR", "VARCHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")


class MariaDBDialect:
    """Traits SQL de MariaDB."""

    def string_type(self, max_length: int) -> str:
        return f"VARCHAR({max_length})"

    def decimal_type(self, precision: int, scale: int) -> str:
        return f"DECIMAL({precision},{scale})"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        return "BIGINT UNSIGNED"

    def identity_storage_type(self) -> str:
        # MariaDB : AUTO_INCREMENT est une clause à part, le type de colonne
        # est déjà un type de stockage ordinaire. Les deux coïncident.
        return "BIGINT UNSIGNED"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        n = sql_type.strip().upper()
        if n == "DATE":
            return ("date",)
        if n in {"DATETIME", "TIMESTAMP"}:
            return ("datetime",)
        for prefix in _INTEGER_PREFIXES:
            if n.startswith(prefix):
                return ("int",)
        for prefix in _FLOAT_PREFIXES:
            if n.startswith(prefix):
                return ("float",)
        for prefix in _STRING_PREFIXES:
            if n.startswith(prefix):
                return ("str",)
        if n in {"BOOL", "BOOLEAN"}:
            return ("bool",)
        return ()

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        return f"{column} {sql_type} NOT NULL AUTO_INCREMENT"

    def auto_increment_clause(self) -> str:
        # MariaDB separe le type et l'auto-increment.
        return "AUTO_INCREMENT"

    def emits_separate_primary_key(self) -> bool:
        return True

    def unique_is_column_constraint(self) -> bool:
        return False

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        return f"UNIQUE KEY uk_{table}_{field_name} ({column})"

    def table_suffix(self) -> str:
        return " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"

    def create_table_opening(self, table: str) -> str:
        return f"CREATE TABLE IF NOT EXISTS {table}"

    def forge_migrations_ddl(self) -> str:
        return (
            "CREATE TABLE IF NOT EXISTS forge_migrations (\n"
            "    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n"
            "    version VARCHAR(64) NOT NULL,\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    filename VARCHAR(255) NOT NULL,\n"
            "    checksum CHAR(64) NOT NULL,\n"
            "    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "    execution_ms INT NULL,\n"
            "    UNIQUE KEY uq_forge_migrations_version (version),\n"
            "    UNIQUE KEY uq_forge_migrations_filename (filename)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )

    def quote_identifier(self, name: str) -> str:
        return f"`{name}`"

    def render_literal(self, value: object) -> str:
        # Booléens 1/0, dates en chaîne ISO quotée (ADR-075).
        return render_literal_value(
            value,
            bool_true="1",
            bool_false="0",
            render_string=escape_string,
            render_date=lambda d: escape_string(d.isoformat()),
            render_datetime=lambda dt: escape_string(dt.strftime("%Y-%m-%d %H:%M:%S")),
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        defs = [
            f"    ADD COLUMN {self.quote_identifier(name)} {definition}"
            for name, definition in columns
        ]
        return f"ALTER TABLE {self.quote_identifier(table)}\n" + ",\n".join(defs) + ";\n"

    def named_unique(self, name: str, columns: "list[str]") -> str:
        return f"UNIQUE KEY {name} ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return True

    def index_clause(self, name: str, column: str) -> str:
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        return f"CREATE INDEX {name} ON {table} ({column});"

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        # Levier de session MariaDB (ADR-077).
        return [f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"]

    # ── DDL du socle Auth/User (ADR-084) ─────────────────────────────────────

    def auto_increment_primary_key_ddl(self, column: str, sql_type: str) -> str:
        return f"{column} {sql_type} AUTO_INCREMENT PRIMARY KEY"

    def char_type(self, length: int) -> str:
        return f"CHAR({length})"

    def boolean_default_literal(self, value: bool) -> str:
        return "TRUE" if value else "FALSE"

    def timestamp_default_clause(self, *, on_update: bool) -> str:
        if on_update:
            return "DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP"
        return "DEFAULT CURRENT_TIMESTAMP"

    def collated_table_suffix(self) -> str:
        return " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"

    # ── DDL des relations many_to_one (ADR-084) ──────────────────────────────

    def add_foreign_key_sql(
        self,
        *,
        table: str,
        column: str,
        sql_type: str,
        nullable: bool,
        ref_table: str,
        ref_column: str,
        constraint_name: str,
        on_delete: str,
        on_update: str,
        index_name: "str | None",
        add_column: bool,
    ) -> "list[str]":
        statements: list[str] = []
        if add_column:
            null_sql = "NULL" if nullable else "NOT NULL"
            statements.append(
                f"ALTER TABLE {table}\n"
                f"    ADD COLUMN {column} {sql_type} {null_sql};"
            )
        statements.append(
            f"ALTER TABLE {table}\n"
            f"    ADD CONSTRAINT {constraint_name}\n"
            f"    FOREIGN KEY ({column})\n"
            f"    REFERENCES {ref_table} ({ref_column})\n"
            f"    ON DELETE {on_delete}\n"
            f"    ON UPDATE {on_update};"
        )
        if index_name is not None:
            statements.append(self.create_index_sql(table, index_name, column))
        return statements

    def introspect_columns(
        self, connection: Any, table: str, database: str
    ) -> "list[tuple[str, str, bool, bool]]":
        cursor = connection.cursor()
        try:
            cursor.execute(
                "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? "
                "ORDER BY ORDINAL_POSITION",
                (database, table),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [
            (
                str(row[0]),
                str(row[1]),
                str(row[2]).upper() == "YES",
                "auto_increment" in str(row[3]).lower(),
            )
            for row in rows
        ]
