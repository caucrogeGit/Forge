# Le dialecte SQL Server

Objectif : comprendre comment Forge traduit le schéma en Transact-SQL.

**Ce que vous allez apprendre :** les particularités du dialecte SQL Server.

Premier palier du **niveau avancé**.

## Clé primaire

SQL Server utilise `BIGINT IDENTITY(1,1)` pour l'identité auto-incrémentée.

## Identifiants

Les identifiants sont entourés de crochets (`[table]`).

## Formes gardées

SQL Server n'a pas `IF NOT EXISTS` pour les tables et les index. Le dialecte émet des formes gardées :

- tables : `IF OBJECT_ID(N'table', N'U') IS NULL CREATE TABLE ...` ;
- index : `IF NOT EXISTS (SELECT 1 FROM sys.indexes ...) CREATE INDEX ...`.

## Paramètres et insertion

`pyodbc` utilise nativement `?` : pas de traduction.
`lastrowid` est obtenu via `SELECT SCOPE_IDENTITY()`.

## Introspection

Le diff de schéma s'appuie sur `INFORMATION_SCHEMA` et `COLUMNPROPERTY` (identité).

!!! note "SQL visible"
    Le SQL reste celui de Forge, exprimé en Transact-SQL ; vous pouvez relire le schéma et les migrations.

## Après cette étape

[Palier suivant : Valider l'intégration](mssql-validate.md)
