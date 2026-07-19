# État du support

Objectif : savoir ce qui est garanti pour SQL Server et ce qui reste à votre charge.

**Ce que vous allez apprendre :** le périmètre exact du niveau de support.

Deuxième palier du **niveau intermédiaire**.

## Niveau plein

`forge-mvc-mssql` est au **niveau plein** (ADR-084, révision du 2026-07-19), comme les autres backends livrés.

## Ce qui est garanti

| Domaine | État |
|---|---|
| Provisioning par `db:init` (`--run`) | fonctionnel (compte `DB_ADMIN_*` existant) |
| Dialecte Transact-SQL (types, DDL) | testé |
| Paramètres `?` (pyodbc natif) | sans traduction |
| Identité d'insertion (`lastrowid`) | fiable (`SCOPE_IDENTITY()` dans le lot de l'INSERT) |
| `db:apply` | fonctionnel |
| `migration:*` | validé en CI (application, idempotence, dry-run, refus `CHANGED`, rollback, introspection) |
| Runtime (`core.database.db`) | validé en CI contre un vrai SQL Server 2022 |

## Ce qui reste à votre charge

| Domaine | État |
|---|---|
| Pilote ODBC système | requis (« ODBC Driver 18 for SQL Server » par défaut, `DB_ODBC_DRIVER`) |
| Compte `DB_ADMIN_*` | doit exister sur le serveur avant `db:init --run` |

À noter : l'escape hatch `DB_APP_PRIVILEGES` au-delà du DML est propre à MariaDB, `db:init` le refuse explicitement sur SQL Server.
Le diff incrémental de schéma compare des noms de types SQL Server et peut rester imparfait.

!!! note "Référence"
    Le niveau de support des backends est défini par l'ADR-084 (révision du 2026-07-19 : promotion au niveau plein).

## Après cette étape

[Bilan du niveau intermédiaire](bilan.md)
