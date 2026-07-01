# pyright: strict
"""forge-mvc-mssql — backend BDD Microsoft SQL Server pour Forge (ADR-054).

Le cœur découvre ce backend via l'entry point ``forge_mvc.db_backend``.
Statut Alpha : la logique de dialecte est testée unitairement ; l'intégration
avec un serveur SQL Server (base client-serveur, pilote ODBC) est à valider
côté développeur. pyodbc utilise nativement les paramètres « ? » de Forge.
"""
from forge_mvc_mssql.backend import MSSQLBackend

__version__ = "1.0.0rc2"

__all__ = ["MSSQLBackend"]
