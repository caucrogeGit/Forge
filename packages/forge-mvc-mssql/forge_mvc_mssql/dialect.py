# pyright: strict
"""
forge_mvc_mssql.dialect — Traits SQL Microsoft SQL Server (ADR-054)
==================================================================
Mapping des types Forge vers SQL Server (Transact-SQL) et primitives DDL.
Particularités : clé primaire auto-incrémentée via ``IDENTITY(1,1)``,
identifiants entre crochets ``[...]``, absence de ``IF NOT EXISTS`` (formes
gardées ``IF OBJECT_ID(...) IS NULL`` / ``IF NOT EXISTS (SELECT ...)``), et
index en instructions séparées.
"""
from typing import Any

from core.database.literals import escape_string, render_literal_value

_SIMPLE_TYPES: dict[str, str] = {
    "text":        "NVARCHAR(MAX)",
    "integer":     "INT",
    "big_integer": "BIGINT",
    "float":       "FLOAT",
    "boolean":     "BIT",
    "date":        "DATE",
    "datetime":    "DATETIME2",
    "email":       "NVARCHAR(255)",
    "password":    "NVARCHAR(255)",
    "slug":        "NVARCHAR(180)",
    "json":        "NVARCHAR(MAX)",
}

_INTEGER_PREFIXES = ("INT", "BIGINT", "SMALLINT", "TINYINT")
_FLOAT_PREFIXES = ("FLOAT", "REAL", "DECIMAL", "NUMERIC", "MONEY")
_STRING_PREFIXES = ("CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "TEXT", "NTEXT", "UNIQUEIDENTIFIER")
_DATETIME_PREFIXES = ("DATETIME", "SMALLDATETIME")


class MSSQLDialect:
    """Traits SQL de Microsoft SQL Server."""

    def string_type(self, max_length: int) -> str:
        return f"NVARCHAR({max_length})"

    def decimal_type(self, precision: int, scale: int) -> str:
        return f"DECIMAL({precision},{scale})"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        return "BIGINT IDENTITY(1,1)"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        n = sql_type.strip().upper()
        if n == "DATE":
            return ("date",)
        for prefix in _DATETIME_PREFIXES:
            if n.startswith(prefix):
                return ("datetime",)
        if n in {"BIT", "BOOL", "BOOLEAN"}:
            return ("bool",)
        for prefix in _INTEGER_PREFIXES:
            if n.startswith(prefix):
                return ("int",)
        for prefix in _FLOAT_PREFIXES:
            if n.startswith(prefix):
                return ("float",)
        for prefix in _STRING_PREFIXES:
            if n.startswith(prefix):
                return ("str",)
        return ()

    # ── DDL ──────────────────────────────────────────────────────────────────

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        # IDENTITY(1,1) gère l'auto-incrément ; le type passé est ignoré.
        return f"{column} BIGINT IDENTITY(1,1)"

    def emits_separate_primary_key(self) -> bool:
        return True

    def unique_is_column_constraint(self) -> bool:
        return True

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        return f"UNIQUE ({column})"

    def table_suffix(self) -> str:
        return ""

    def create_table_opening(self, table: str) -> str:
        # SQL Server n'a pas CREATE TABLE IF NOT EXISTS.
        return f"IF OBJECT_ID(N'{table}', N'U') IS NULL\nCREATE TABLE {table}"

    def forge_migrations_ddl(self) -> str:
        return (
            "IF OBJECT_ID(N'forge_migrations', N'U') IS NULL\n"
            "CREATE TABLE forge_migrations (\n"
            "    id BIGINT IDENTITY(1,1) PRIMARY KEY,\n"
            "    version NVARCHAR(64) NOT NULL,\n"
            "    name NVARCHAR(255) NOT NULL,\n"
            "    filename NVARCHAR(255) NOT NULL,\n"
            "    checksum CHAR(64) NOT NULL,\n"
            "    applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),\n"
            "    execution_ms INT,\n"
            "    CONSTRAINT uq_forge_migrations_version UNIQUE (version),\n"
            "    CONSTRAINT uq_forge_migrations_filename UNIQUE (filename)\n"
            ")"
        )

    def quote_identifier(self, name: str) -> str:
        return f"[{name}]"

    def render_literal(self, value: object) -> str:
        # SQL Server : chaînes Unicode N'...', booléens (BIT) 1/0, dates ISO (ADR-075).
        return render_literal_value(
            value,
            bool_true="1",
            bool_false="0",
            render_string=lambda s: escape_string(s, national=True),
            render_date=lambda d: escape_string(d.isoformat()),
            render_datetime=lambda dt: escape_string(dt.strftime("%Y-%m-%d %H:%M:%S")),
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        # SQL Server : un seul ALTER TABLE ... ADD col def, col def (sans COLUMN).
        defs = [
            f"{self.quote_identifier(name)} {definition}"
            for name, definition in columns
        ]
        return (
            f"ALTER TABLE {self.quote_identifier(table)}\n"
            "    ADD " + ",\n        ".join(defs) + ";\n"
        )

    def named_unique(self, name: str, columns: "list[str]") -> str:
        return f"CONSTRAINT {name} UNIQUE ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return False

    def index_clause(self, name: str, column: str) -> str:
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        # SQL Server n'a pas CREATE INDEX IF NOT EXISTS : forme gardée.
        return (
            f"IF NOT EXISTS (SELECT 1 FROM sys.indexes "
            f"WHERE name = '{name}' AND object_id = OBJECT_ID('{table}'))\n"
            f"    CREATE INDEX {name} ON {table} ({column});"
        )

    def introspect_columns(
        self, connection: Any, table: str, database: str
    ) -> "list[tuple[str, str, bool, bool]]":
        cursor = connection.cursor()
        try:
            # pyodbc utilise nativement les paramètres « ? ».
            cursor.execute(
                "SELECT c.COLUMN_NAME, c.DATA_TYPE, c.IS_NULLABLE, "
                "COLUMNPROPERTY(OBJECT_ID(?), c.COLUMN_NAME, 'IsIdentity') "
                "FROM INFORMATION_SCHEMA.COLUMNS c "
                "WHERE c.TABLE_NAME = ? "
                "ORDER BY c.ORDINAL_POSITION",
                (table, table),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [
            (
                str(row[0]),
                str(row[1]).upper(),
                str(row[2]).upper() == "YES",
                bool(row[3]),
            )
            for row in rows
        ]
