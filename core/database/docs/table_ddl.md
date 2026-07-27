# Rendu dialectal d'une table d'infrastructure

Ce document décrit `core/database/table_ddl.py`.

## À quoi cela sert

Un paquet Forge qui livre sa propre table (sessions, jobs, audit, notifications…) doit pouvoir la décrire **une fois** et obtenir le DDL correct pour le backend actif.

Sans ce rendu, chaque paquet écrivait son SQL à la main, et l'écrivait pour MariaDB.
L'audit `OPTIN-DDL-DIALECT-AUDIT-001` a mesuré le coût sur quatre serveurs réels : douze fichiers SQL livrés par dix opt-ins, aucun exécutable ailleurs que sur MariaDB, alors que le contrat `Dialect` couvrait déjà toutes les constructions en cause.

## Ce que le rendu produit

`render_create_table(table, dialect)` retourne une **liste d'instructions** à exécuter dans l'ordre : le `CREATE TABLE`, puis les `CREATE INDEX` que le dialecte exige hors de la création.

MariaDB porte ses index dans le `CREATE TABLE` ; PostgreSQL, SQLite et SQL Server les veulent séparés.
Le rendu s'en charge, l'appelant n'a pas à le savoir.

Le SQL reste **visible** (principe 5) : la commande `<opt-in>:init` écrit le texte produit dans `mvc/migrations/`, où l'auteur le relit avant de l'appliquer (ADR-071).

## Décrire une table

```python
from core.database.table_ddl import Column, Index, TableDefinition, render_create_table
from core.database.backend import get_backend

FORGE_SESSIONS = TableDefinition(
    name="forge_sessions",
    columns=[
        Column("session_id", "char", length=64),
        Column("data", "text"),
        Column("expire_at", "datetime"),
        Column("version", "integer", default=0),
    ],
    primary_key=["session_id"],
    indexes=[Index("idx_forge_sessions_expire_at", "expire_at")],
)

statements = render_create_table(FORGE_SESSIONS, get_backend().dialect)
```

## Types acceptés

Les types sont exprimés en vocabulaire **Forge**, jamais en SQL d'un SGBD.

| Type | Rendu par | Remarque |
|---|---|---|
| `string` | `Dialect.string_type(length)` | `length` requis |
| `char` | `Dialect.char_type(length)` | `length` requis |
| `text`, `integer`, `big_integer`, `float`, `boolean`, `date`, `datetime`, `json` | `Dialect.simple_type(...)` | |
| `identity` | `Dialect.auto_increment_column_ddl(...)` | clé primaire auto-incrémentée |
| `identity_ref` | `Dialect.identity_storage_type()` | référence vers une identité, jamais auto-incrémentée |

La distinction `identity` / `identity_ref` est celle du ticket `FK-IDENTITY-STORAGE-TYPE-001` : une colonne qui **stocke** un identifiant ne doit pas en **générer** un.

## Valeurs par défaut

`NO_DEFAULT` est la sentinelle d'absence, distincte de `DEFAULT NULL` : une colonne peut légitimement valoir `NULL` par défaut.

`default_now=True` rend `DEFAULT CURRENT_TIMESTAMP` via le dialecte.
Avec `on_update_now=True`, la mise à jour automatique est ajoutée **là où le dialecte la connaît** ; ailleurs le simple `DEFAULT` est rendu et c'est à l'application de tenir l'horloge.

## Clés étrangères

`ON DELETE RESTRICT` est normalisé en `NO ACTION` : SQL Server ne connaît pas `RESTRICT`, alors que `NO ACTION` est compris par les quatre backends et a la même sémantique pratique.

## Ce que ce module ne fait pas

Il rend des **tables d'infrastructure**, livrées figées par un paquet.

Les entités de l'application ont leur propre chaîne, `forge_mvc_entities.build_entity_sql`, qui part d'un contrat JSON utilisateur et gère bien davantage : relations, médias, slugs, horodatages gérés.
Les deux rendus partagent le contrat `Dialect` mais pas leur entrée.
Les confondre reviendrait à faire dépendre tous les opt-ins du moteur d'entités.

## Garde-fou

`tests/meta/test_optin_ddl_portability_ratchet_001.py` est un **cliquet** : la liste des fichiers SQL encore non portables ne peut que diminuer.
Un paquet neuf qui livrerait du SQL propre à MariaDB fait échouer la suite, et un fichier corrigé mais laissé dans la liste la fait échouer aussi.
