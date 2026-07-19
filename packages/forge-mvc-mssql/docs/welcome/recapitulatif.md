# Aide-mémoire SQL Server

Synthèse du backend `forge-mvc-mssql`.

## Installer et activer

```bash
pip install --pre forge-mvc-mssql
```

Découvert automatiquement ; si plusieurs backends : `DB_BACKEND=mssql`.
Un serveur SQL Server et un pilote ODBC sont requis.

## Provisionner

```bash
forge db:init        # affiche le SQL de provisioning (lots séparés par GO)
forge db:init --run  # l'exécute avec DB_ADMIN_* (compte existant)
```

## Cycle de la base

| Étape | Commande |
|---|---|
| Provisionner base + comptes | `forge db:init --run` |
| Appliquer le schéma | `forge db:apply` |
| État des migrations | `forge migration:status` |
| Créer une migration | `forge migration:make <nom>` |
| Appliquer les migrations | `forge migration:apply` |

## À retenir

- backend SQL Server via `pyodbc` (pilote ODBC requis), **niveau plein** (ADR-084) ;
- `?` natifs ; identité `BIGINT IDENTITY(1,1)` ; crochets ; formes gardées ;
- provisioning par `forge db:init` (`--run` pour exécuter, avec `DB_ADMIN_*`) ;
- intégration validée en CI contre un vrai SQL Server 2022 ;
- un seul backend par projet (ADR-054).

## Voir aussi

- [Référence](../reference.md) : contrat, dialecte, statut.
