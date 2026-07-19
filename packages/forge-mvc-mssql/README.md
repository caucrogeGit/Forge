# forge-mvc-mssql

Backend BDD **Microsoft SQL Server** pour [Forge](https://forgemvc.com), au-dessus
de `pyodbc`.

Depuis l'ADR-054, le cœur de Forge est agnostique BDD : il découvre le backend
installé via un entry point. Ce paquet ajoute **SQL Server** à la liste des
choix de SGBD du développeur.

!!! note "Niveau plein"
    Backend au **niveau plein** (ADR-084, révision du 2026-07-19).
    `forge db:init` provisionne SQL Server (`--run` pour exécuter), l'identité d'insertion est fiable, et l'intégration est validée en CI contre un vrai SQL Server 2022 (pilote ODBC Driver 18).

## Installation

```bash
pip install forge-mvc forge-mvc-mssql
```

SQL Server est **client-serveur** : un serveur SQL Server doit être joignable
(installé, en conteneur `mcr.microsoft.com/mssql/server`, ou distant), et un
**pilote ODBC** doit être présent sur la machine cliente (par défaut
« ODBC Driver 18 for SQL Server », surchargeable via `DB_ODBC_DRIVER`).

## Particularités gérées

- **Paramètres** : pyodbc utilise nativement les `?` de Forge (aucune traduction).
- **Identité** : clé primaire auto-incrémentée via `BIGINT IDENTITY(1,1)`.
- **Insertion** : `lastrowid` via `SCOPE_IDENTITY()`, exécuté dans le même
  lot que l'INSERT.
- **Identifiants** : entre crochets `[...]`.
- **Idempotence** : SQL Server n'a pas `IF NOT EXISTS` ; le dialecte émet des
  formes gardées (`IF OBJECT_ID(...) IS NULL` pour les tables, `IF NOT EXISTS
  (SELECT ... FROM sys.indexes ...)` pour les index).
- **Lignes-dict** : pyodbc ne renvoie pas de dictionnaires ; l'adaptateur
  convertit via `cursor.description`.

## Configuration

Connexion via l'environnement (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`,
`DB_APP_PWD`, et `DB_ODBC_DRIVER` au besoin). Un seul backend BDD par projet.

## Provisioning

`forge db:init` génère et affiche le SQL de provisioning SQL Server
(logins d'administration et applicatif, base, users, `GRANT` sur
`SCHEMA::dbo`, table `forge_migrations`), en lots séparés par `GO` pour
`sqlcmd`.
`forge db:init --run` l'exécute avec le compte `DB_ADMIN_*` (qui doit
exister sur le serveur) : la base, la connexion et l'utilisateur
applicatifs et le registre des migrations sont créés.

## Limites connues

- L'escape hatch `DB_APP_PRIVILEGES` au-delà du DML (SELECT, INSERT,
  UPDATE, DELETE) est propre à MariaDB : refus explicite sur SQL Server.
- L'introspection de diff compare des noms de types SQL Server : le suivi
  incrémental de schéma peut être imparfait.

## Licence

Propriétaire (voir `LICENSE`). Trajectoire MIT visée à la version 1.0.0 stable.
