# pyright: strict
"""forge-mvc-sqlite — backend BDD SQLite pour Forge (ADR-054).

Le cœur découvre ce backend via l'entry point ``forge_mvc.db_backend``.
L'API publique se réduit au backend lui-même.
"""
from forge_mvc_sqlite.backend import SQLiteBackend

__version__ = "1.0.0rc5"

__all__ = ["SQLiteBackend"]
