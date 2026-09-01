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

## Ajouter une colonne à une table déjà provisionnée

`render_create_table` ne suffit pas quand la table existe déjà chez l'exploitant.
Sa migration de création ne se rejoue pas, son empreinte étant enregistrée, si bien qu'un opt-in ne pouvait pas faire évoluer son schéma sans casser les projets en place.

`render_add_column(table, column_name, dialect)` rend l'ajout, et `AddColumn` le déclare dans la liste `MIGRATIONS` d'un paquet.

```python
from core.database.table_ddl import AddColumn

MIGRATIONS = [
    ("20260710130000_create_forge_sessions.sql", FORGE_SESSIONS),
    ("20260901090000_add_user_id_to_forge_sessions.sql", AddColumn(FORGE_SESSIONS, "user_id")),
]
```

`table` porte la définition **à jour**, colonne comprise, pour qu'une seule description reste la source.

!!! warning "La colonne doit accepter NULL, ou porter un défaut"
    Les lignes déjà présentes doivent pouvoir la satisfaire.

    Une colonne `NOT NULL` sans défaut est refusée au rendu, plutôt que de faire échouer la migration chez l'exploitant.

!!! info "Les index sont toujours rendus séparément"
    Un `ALTER TABLE` ne porte pas d'index, y compris sur les dialectes qui les inlinent dans un `CREATE TABLE`.

    Seuls les index de la colonne ajoutée sont rendus.
    Rendre les autres créerait un doublon, que MariaDB refuse et que PostgreSQL et SQL Server ignorent en silence.

!!! danger "SQL Server n'écrit pas `ADD COLUMN`"
    Sa syntaxe est `ALTER TABLE t ADD colonne type`, sans le mot-clé.
    Celui-ci y produit « Incorrect syntax near the keyword 'COLUMN' », et l'instruction est refusée par le serveur.

    La clause vient donc du contrat `Dialect`, via `add_column_clause`.
    Le défaut n'est apparu qu'en jouant la migration contre un vrai serveur : une comparaison de chaînes ne montre jamais qu'une instruction bien formée est refusée.

## Ce que ce module ne fait pas

Il rend des **tables d'infrastructure**, livrées figées par un paquet.

Les entités de l'application ont leur propre chaîne, `forge_mvc_entities.build_entity_sql`, qui part d'un contrat JSON utilisateur et gère bien davantage : relations, médias, slugs, horodatages gérés.
Les deux rendus partagent le contrat `Dialect` mais pas leur entrée.
Les confondre reviendrait à faire dépendre tous les opt-ins du moteur d'entités.

## Garde-fou

`tests/db/test_add_column_migration_real_server_001.py` joue l'ajout de colonne contre les trois serveurs, création puis migration, avec une ligne écrite avant.

`tests/meta/test_optin_ddl_portability_ratchet_001.py` est un **cliquet** : la liste des fichiers SQL encore non portables ne peut que diminuer.
Un paquet neuf qui livrerait du SQL propre à MariaDB fait échouer la suite, et un fichier corrigé mais laissé dans la liste la fait échouer aussi.
