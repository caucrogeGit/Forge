# pyright: strict
"""forge-mvc-mssql — backend BDD Microsoft SQL Server pour Forge (ADR-054).

Le cœur découvre ce backend via l'entry point ``forge_mvc.db_backend``.
Niveau plein (promotion ADR-084) : dialecte, provisioning ``db:init`` et
intégration serveur (couche DB, migrations, pilote ODBC) validés en CI contre
un vrai SQL Server. pyodbc utilise nativement les paramètres « ? » de Forge.
"""
from forge_mvc_mssql.backend import MSSQLBackend

__version__ = "1.0.0rc7"

__all__ = ["MSSQLBackend"]
