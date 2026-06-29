# SQL Server (forge-mvc-mssql)

`forge-mvc-mssql` est un backend de base de données pour Forge, au-dessus de `pyodbc`, pour faire fonctionner la couche BDD du cœur sur Microsoft SQL Server.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.

!!! warning "Statut Alpha"
    Dialecte Transact-SQL testé unitairement ; intégration serveur (pilote ODBC) et provisioning CLI à valider/câbler.

    Créez la base et le login à la main, puis utilisez `db:apply` / `migration:*`.

## En bref

- backend SQL Server via `pyodbc` (pilote ODBC requis) ;
- paramètres `?` natifs (aucune traduction) ;
- identité `BIGINT IDENTITY(1,1)`, identifiants entre crochets ;
- provisioning CLI pas encore câblé (base + login manuels).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, statut Alpha.
- [Progression SQL Server](welcome/installation.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-mssql
```
