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
