# Les deux comptes

Objectif : comprendre pourquoi Forge sépare le compte d'administration et le compte applicatif.

**Ce que vous allez apprendre :** la structure (DDL) et l'exécution (DML) n'utilisent pas le même compte (ADR-033).

Deuxième palier du **niveau intermédiaire**.

## Pourquoi deux comptes

| Compte | Variables | Usage |
|---|---|---|
| Administration | `DB_ADMIN_*` | `db:init`, `db:apply`, `migration:*` (création et modification de structure) |
| Applicatif | `DB_APP_*` | runtime de l'application (DML : `SELECT`/`INSERT`/`UPDATE`/`DELETE`) |

## Le principe

Le compte runtime est **limité au DML** : l'application ne peut pas modifier la structure en exécution.

Les changements de structure passent par les commandes CLI, avec le compte admin, de façon explicite et tracée (`forge_migrations`).

!!! note "Sécurité par défaut"
    Restreindre `DB_APP_*` au DML réduit l'impact d'une faille applicative : pas de `DROP TABLE` possible depuis une requête web.

!!! warning "Droits du compte admin"
    `DB_ADMIN_*` doit pouvoir créer base, utilisateur et accorder des privilèges pour `db:init`.

    En production, ces opérations se font une fois, à la mise en place.

## Après cette étape

[Bilan du niveau intermédiaire](bilan.md)
