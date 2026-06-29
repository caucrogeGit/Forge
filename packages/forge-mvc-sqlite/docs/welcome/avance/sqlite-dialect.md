# Le dialecte SQLite

Objectif : comprendre comment Forge traduit le schéma en SQL SQLite.

**Ce que vous allez apprendre :** chaque backend a un dialecte ; celui de SQLite a des particularités par rapport à MariaDB.

Premier palier du **niveau avancé**.

## Ce que ce palier montre

- la clé primaire auto-incrémentée en SQLite ;
- les index en instructions séparées ;
- les affinités de types.

## Clé primaire

SQLite utilise `INTEGER PRIMARY KEY AUTOINCREMENT`, portée sur la colonne, là où MariaDB ajoute une clause `PRIMARY KEY` séparée.

## Index

SQLite n'accepte pas de déclaration d'index à l'intérieur du `CREATE TABLE` : Forge émet des instructions `CREATE INDEX` **séparées** après la table.

## Types

SQLite raisonne par **affinités** (`TEXT`, `INTEGER`, `REAL`, `NUMERIC`) plutôt que par types stricts. Le dialecte mappe les types Forge vers ces affinités, et la validation d'entité reste cohérente (un `datetime` stocké en `TEXT` est accepté).

!!! note "SQL visible"
    Le dialecte produit du SQL lisible : vous pouvez relire le schéma généré et les migrations.

## Après cette étape

[Palier suivant : Quand choisir SQLite](sqlite-when.md)
