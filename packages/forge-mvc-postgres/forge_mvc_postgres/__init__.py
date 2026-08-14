# pyright: strict
"""forge-mvc-postgres — backend BDD PostgreSQL pour Forge (ADR-054).

Le cœur découvre ce backend via l'entry point ``forge_mvc.db_backend``.
Niveau plein (promotion ADR-084) : dialecte, traduction de paramètres,
provisioning ``db:init`` et intégration serveur (couche DB, migrations)
validés en CI contre un vrai PostgreSQL.
"""
from forge_mvc_postgres.backend import PostgreSQLBackend

__version__ = "1.0.0rc6"

__all__ = ["PostgreSQLBackend"]
