# pyright: strict
"""
forge_mvc_sqlite.dialect — Traits SQL SQLite (ADR-054)
======================================================
Mapping des types Forge vers les affinités de colonne SQLite. SQLite a un
typage par affinité (TEXT, INTEGER, REAL, NUMERIC) : pas de longueur, pas de
type booléen ni date/heure natifs (stockés en TEXT ISO ou entier 0/1).
"""

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
