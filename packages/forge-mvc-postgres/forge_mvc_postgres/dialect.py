# pyright: strict
"""
forge_mvc_postgres.dialect — Traits SQL PostgreSQL (ADR-054)
============================================================
Mapping des types Forge vers PostgreSQL et primitives DDL. La clé primaire
auto-incrémentée utilise BIGSERIAL ; les index sont des instructions CREATE
INDEX séparées (PostgreSQL n'accepte pas d'index dans le CREATE TABLE).
"""
from typing import Any

from core.database.literals import escape_string, render_literal_value

_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INTEGER",
    "big_integer": "BIGINT",
    "float":       "DOUBLE PRECISION",
    "boolean":     "BOOLEAN",
    "date":        "DATE",
    "datetime":    "TIMESTAMP",
    "email":       "VARCHAR(255)",
    "password":    "VARCHAR(255)",
    "slug":        "VARCHAR(180)",
    "json":        "JSONB",
}

# Préfixes de types PostgreSQL par famille Python (validation sql/python).
_INTEGER_PREFIXES = ("INT", "BIGINT", "SMALLINT", "BIGSERIAL", "SERIAL", "SMALLSERIAL")
_FLOAT_PREFIXES = ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")
_STRING_PREFIXES = ("CHAR", "VARCHAR", "TEXT", "JSON", "JSONB", "UUID")


class PostgreSQLDialect:
    """Traits SQL de PostgreSQL."""

    def string_type(self, max_length: int) -> str:
        return f"VARCHAR({max_length})"

    def decimal_type(self, precision: int, scale: int) -> str:
        return f"NUMERIC({precision},{scale})"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        return "BIGSERIAL"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        n = sql_type.strip().upper()
        if n == "DATE":
            return ("date",)
        if n.startswith("TIMESTAMP"):
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

    # ── DDL ──────────────────────────────────────────────────────────────────

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        # BIGSERIAL crée la séquence et implique NOT NULL ; le type passé est
        # ignoré (la PK auto-incrémentée est toujours un serial).
        return f"{column} BIGSERIAL"

    def emits_separate_primary_key(self) -> bool:
        return True

    def unique_is_column_constraint(self) -> bool:
        # Unicité portée par la colonne, pour éviter les soucis d'ordre des
        # contraintes de table.
        return True

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        return f"UNIQUE ({column})"

    def table_suffix(self) -> str:
        return ""

    def create_table_opening(self, table: str) -> str:
        return f"CREATE TABLE IF NOT EXISTS {table}"

    def forge_migrations_ddl(self) -> str:
        return (
            "CREATE TABLE IF NOT EXISTS forge_migrations (\n"
            "    id BIGSERIAL PRIMARY KEY,\n"
            "    version VARCHAR(64) NOT NULL,\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    filename VARCHAR(255) NOT NULL,\n"
            "    checksum CHAR(64) NOT NULL,\n"
            "    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "    execution_ms INTEGER,\n"
            "    UNIQUE (version),\n"
            "    UNIQUE (filename)\n"
            ")"
        )

    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def render_literal(self, value: object) -> str:
        # PostgreSQL : booléens TRUE/FALSE, dates typées DATE '...' / TIMESTAMP '...' (ADR-075).
        return render_literal_value(
            value,
            bool_true="TRUE",
            bool_false="FALSE",
            render_string=escape_string,
            render_date=lambda d: f"DATE {escape_string(d.isoformat())}",
            render_datetime=lambda dt: f"TIMESTAMP {escape_string(dt.strftime('%Y-%m-%d %H:%M:%S'))}",
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        defs = [
            f"    ADD COLUMN {self.quote_identifier(name)} {definition}"
            for name, definition in columns
        ]
        return f"ALTER TABLE {self.quote_identifier(table)}\n" + ",\n".join(defs) + ";\n"

    def named_unique(self, name: str, columns: "list[str]") -> str:
        return f"CONSTRAINT {name} UNIQUE ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return False

    def index_clause(self, name: str, column: str) -> str:
        # Non utilisé (index hors CREATE TABLE) ; fourni pour le contrat.
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        return f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column});"

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        # PostgreSQL n'a pas d'interrupteur FK ; session_replication_role =
        # replica court-circuite les triggers (dont les contraintes FK). Exige un
        # rôle superuser (ADR-077).
        return [f"SET session_replication_role = {'origin' if enabled else 'replica'}"]

    def introspect_columns(
        self, connection: Any, table: str, database: str
    ) -> "list[tuple[str, str, bool, bool]]":
        cursor = connection.cursor()
        try:
            # Paramètres « ? » : l'adaptateur de connexion les traduit en « %s ».
            cursor.execute(
                "SELECT column_name, data_type, is_nullable, column_default "
                "FROM information_schema.columns "
                "WHERE table_name = ? "
                "ORDER BY ordinal_position",
                (table,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [
            (
                str(row[0]),
                str(row[1]),
                str(row[2]).upper() == "YES",
                str(row[3] or "").lower().startswith("nextval"),
            )
            for row in rows
        ]
