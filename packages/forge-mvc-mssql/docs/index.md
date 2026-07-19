# SQL Server (forge-mvc-mssql)

`forge-mvc-mssql` est un backend de base de données pour Forge, au-dessus de `pyodbc`, pour faire fonctionner la couche BDD du cœur sur Microsoft SQL Server.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.

!!! note "Niveau plein"
    Backend au **niveau plein** (ADR-084, révision du 2026-07-19) : provisioning par `db:init`, identité d'insertion fiable, intégration validée en CI contre un vrai SQL Server 2022.

    Un pilote ODBC système reste requis (« ODBC Driver 18 for SQL Server » par défaut, surchargeable via `DB_ODBC_DRIVER`).

## En bref

- backend SQL Server via `pyodbc` (pilote ODBC requis) ;
- paramètres `?` natifs (aucune traduction) ;
- identité `BIGINT IDENTITY(1,1)`, identifiants entre crochets ;
- `db:init` provisionne base, comptes et registre des migrations (`--run` pour exécuter).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, statut.
- [Progression SQL Server](welcome/debutant/mssql-welcome.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-mssql
```
