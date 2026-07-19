# État du support

Objectif : connaître le niveau de support de PostgreSQL dans Forge.

**Ce que vous allez apprendre :** ce que garantit le niveau plein (ADR-084) pour ce backend.

Deuxième palier du **niveau intermédiaire**.

## Le niveau plein

PostgreSQL est un backend au **niveau plein** depuis la révision de l'ADR-084 du 2026-07-19.
Ce niveau signifie que les chemins de génération SQL passent par le dialecte PostgreSQL et que l'intégration est prouvée contre un vrai serveur.

## Ce qui est garanti

| Domaine | État |
|---|---|
| Provisioning par `db:init` | câblé : SQL affiché, `--run` l'exécute |
| Identité d'insertion (`lastrowid`) | fiable : `lastval()` sous garde savepoint |
| Couche BDD (insertion, lecture, `rowcount`, anti-injection, transactions, clés étrangères) | validée en CI contre PostgreSQL 16 |
| Runner de migrations (application, idempotence, dry-run, refus CHANGED, rollback réel, introspection) | validé en CI contre PostgreSQL 16 |
| `db:apply` / `migration:*` | fonctionnels |
| Runtime (`core.database.db`) | fonctionnel (connexion psycopg) |

## Limites

| Domaine | État |
|---|---|
| `DB_APP_PRIVILEGES` au-delà du DML | propre à MariaDB : refus explicite sur PostgreSQL |
| Diff incrémental de schéma | imparfait (noms de types PostgreSQL) |

!!! note "Référence"
    Le niveau de support des backends BDD est défini par l'ADR-084.

    Les quatre backends livrés sont au niveau plein depuis la révision du 2026-07-19.

## Après cette étape

[Bilan du niveau intermédiaire](bilan.md)
