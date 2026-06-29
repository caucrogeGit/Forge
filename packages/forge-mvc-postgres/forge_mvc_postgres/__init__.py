# pyright: strict
"""forge-mvc-postgres — backend BDD PostgreSQL pour Forge (ADR-054).

Le cœur découvre ce backend via l'entry point ``forge_mvc.db_backend``.
Statut Alpha : la logique de dialecte et la traduction de paramètres sont
testées unitairement ; l'intégration avec un serveur PostgreSQL est à valider
côté développeur (base client-serveur, voir README).
"""
from forge_mvc_postgres.backend import PostgreSQLBackend

__version__ = "1.0.0rc1"

__all__ = ["PostgreSQLBackend"]
