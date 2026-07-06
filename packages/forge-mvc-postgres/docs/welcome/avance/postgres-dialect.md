# Le dialecte PostgreSQL

Objectif : comprendre comment Forge traduit le schéma en SQL PostgreSQL.

**Ce que vous allez apprendre :** les particularités du dialecte et de l'adaptateur psycopg.

Premier palier du **niveau avancé**.

## Clé primaire

PostgreSQL utilise `BIGSERIAL` pour l'identité auto-incrémentée (séquence implicite).

## Index

Comme SQLite, PostgreSQL n'accepte pas d'index dans le `CREATE TABLE` : Forge émet des `CREATE INDEX` **séparés**.

## Identifiants et types

Les identifiants sont entre guillemets doubles (`"table"`).
L'introspection (diff de migrations) passe par `information_schema`.

## Paramètres

Forge génère des paramètres `?` ; l'adaptateur les traduit en `%s` (format psycopg), en préservant les littéraux chaîne et en doublant les `%` littéraux.

## Insertion

PostgreSQL n'a pas de `lastrowid` natif : l'adaptateur lit la dernière valeur de séquence via `SELECT lastval()`.

!!! note "SQL visible"
    Le SQL reste celui de Forge ; seule la forme des paramètres est adaptée à psycopg.

## Après cette étape

[Palier suivant : Valider l'intégration](postgres-validate.md)
