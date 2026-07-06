# Aide-mémoire SQL Server

Synthèse du backend `forge-mvc-mssql` (Alpha).

## Installer et activer

```bash
pip install --pre forge-mvc-mssql
```

Découvert automatiquement ; si plusieurs backends : `DB_BACKEND=mssql`.
Un serveur SQL Server et un pilote ODBC sont requis.

## Préparer (Alpha : manuel)

```sql
CREATE DATABASE mon_projet;
CREATE LOGIN mon_projet WITH PASSWORD = '...';
-- puis CREATE USER + rôles dans la base
```

## Cycle de la base

| Étape | Commande |
|---|---|
| Appliquer le schéma | `forge db:apply` |
| État des migrations | `forge migration:status` |
| Créer une migration | `forge migration:make <nom>` |
| Appliquer les migrations | `forge migration:apply` |

## À retenir

- backend SQL Server via `pyodbc` (pilote ODBC requis), statut **Alpha** ;
- `?` natifs ; identité `BIGINT IDENTITY(1,1)` ; crochets ; formes gardées ;
- provisioning `db:init` **non câblé** : base + login à la main ;
- intégration à valider sur un serveur réel ;
- un seul backend par projet (ADR-054).

## Voir aussi

- [Référence](../reference.md) : contrat, dialecte, statut.
