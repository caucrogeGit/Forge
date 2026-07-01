# pyright: strict
"""forge-mvc-mariadb — backend BDD MariaDB pour Forge (ADR-054).

Le cœur découvre ce backend via l'entry point ``forge_mvc.db_backend``.
L'API publique se réduit au backend lui-même.
"""
from forge_mvc_mariadb.backend import MariaDBBackend

__version__ = "1.0.0rc2"

__all__ = ["MariaDBBackend"]
