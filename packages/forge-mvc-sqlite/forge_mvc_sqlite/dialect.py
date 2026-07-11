# pyright: strict
"""
forge_mvc_sqlite.dialect — Traits SQL SQLite (ADR-054)
======================================================
Mapping des types Forge vers les affinités de colonne SQLite. SQLite a un
typage par affinité (TEXT, INTEGER, REAL, NUMERIC) : pas de longueur, pas de
type booléen ni date/heure natifs (stockés en TEXT ISO ou entier 0/1).
"""
import re
from typing import Any

from core.database.literals import escape_string, render_literal_value

_SAFE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# Types Forge « simples » → affinité SQLite.
_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INTEGER",
    "big_integer": "INTEGER",
    "float":       "REAL",
    "boolean":     "INTEGER",
    "date":        "TEXT",
    "datetime":    "TEXT",
    "email":       "TEXT",
    "password":    "TEXT",
    "slug":        "TEXT",
    "json":        "TEXT",
}


class SQLiteDialect:
    """Traits SQL de SQLite (typage par affinité)."""

    def string_type(self, max_length: int) -> str:
        # SQLite ignore la longueur (affinité TEXT).
        return "TEXT"

    def decimal_type(self, precision: int, scale: int) -> str:
        return "NUMERIC"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        # La clé primaire auto-incrémentée SQLite doit être de type INTEGER.
        return "INTEGER"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        # Affinités SQLite : une même affinité couvre plusieurs familles Python
        # (TEXT stocke aussi dates et JSON ; INTEGER stocke aussi les booléens).
        n = sql_type.strip().upper()
        if n == "INTEGER":
            return ("int", "bool")
        if n == "REAL":
            return ("float",)
        if n == "NUMERIC":
            return ("float",)
        if n == "TEXT":
            return ("str", "date", "datetime")
        return ()

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        # SQLite : la PK auto-incrémentée est portée par la colonne elle-même.
        return f"{column} {sql_type} PRIMARY KEY AUTOINCREMENT"

    def emits_separate_primary_key(self) -> bool:
        return False

    def unique_is_column_constraint(self) -> bool:
        # SQLite : l'unicité est portée par la colonne (contraintes de table
        # après toutes les colonnes seulement) — voir build_entity_sql.
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
            "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "    version TEXT NOT NULL,\n"
            "    name TEXT NOT NULL,\n"
            "    filename TEXT NOT NULL,\n"
            "    checksum TEXT NOT NULL,\n"
            "    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "    execution_ms INTEGER,\n"
            "    UNIQUE (version),\n"
            "    UNIQUE (filename)\n"
            ")"
        )

    def quote_identifier(self, name: str) -> str:
        return f'"{name}"'

    def render_literal(self, value: object) -> str:
        # SQLite : pas de booléen ni de date natifs (0/1 et chaîne ISO), ADR-075.
        return render_literal_value(
            value,
            bool_true="1",
            bool_false="0",
            render_string=escape_string,
            render_date=lambda d: escape_string(d.isoformat()),
            render_datetime=lambda dt: escape_string(dt.strftime("%Y-%m-%d %H:%M:%S")),
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        # SQLite : une seule colonne ajoutée par ALTER TABLE.
        return "".join(
            f"ALTER TABLE {self.quote_identifier(table)} "
            f"ADD COLUMN {self.quote_identifier(name)} {definition};\n"
            for name, definition in columns
        )

    def named_unique(self, name: str, columns: "list[str]") -> str:
        # SQLite : contrainte d'unicité sans nom (les noms d'index se déclarent
        # via CREATE INDEX/UNIQUE INDEX séparés).
        return f"UNIQUE ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return False

    def index_clause(self, name: str, column: str) -> str:
        # Non utilisé en SQLite (index hors CREATE TABLE) ; fourni pour le contrat.
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        return f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column});"

    def introspect_columns(
        self, connection: Any, table: str, database: str
    ) -> "list[tuple[str, str, bool, bool]]":
        # PRAGMA n'accepte pas de paramètre lié : on valide le nom de table.
        if not _SAFE_IDENTIFIER.fullmatch(table):
            raise ValueError(f"Nom de table SQLite invalide : {table!r}")
        cursor = connection.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
        finally:
            cursor.close()
        # row : (cid, name, type, notnull, dflt_value, pk)
        return [
            (
                str(row[1]),
                str(row[2]),
                int(row[3]) == 0,
                bool(row[5]) and str(row[2]).upper() == "INTEGER",
            )
            for row in rows
        ]
