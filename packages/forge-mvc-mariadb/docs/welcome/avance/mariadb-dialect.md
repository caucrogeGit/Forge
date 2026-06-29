# Le dialecte MariaDB

Objectif : comprendre comment Forge traduit le schéma en SQL MariaDB.

**Ce que vous allez apprendre :** le dialecte MariaDB est la référence ; les autres backends s'y comparent.

Premier palier du **niveau avancé**.

## Ce que ce palier montre

- la clé primaire auto-incrémentée ;
- le moteur et l'encodage ;
- les index dans le `CREATE TABLE`.

## Clé primaire

MariaDB utilise `INT ... AUTO_INCREMENT` avec une clause `PRIMARY KEY` séparée dans le `CREATE TABLE`.

## Moteur et encodage

Les tables sont créées avec `ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci` : transactions et Unicode complet (emojis inclus).

## Index

MariaDB accepte les déclarations d'index **dans** le `CREATE TABLE`, contrairement à SQLite qui exige des `CREATE INDEX` séparés.

## Identifiants

Les identifiants sont entourés de backticks (`` `table` ``).

!!! note "SQL visible"
    Le dialecte produit du SQL MariaDB lisible : vous pouvez relire le schéma et les migrations.

## Après cette étape

[Palier suivant : Vers la production](mariadb-prod.md)
