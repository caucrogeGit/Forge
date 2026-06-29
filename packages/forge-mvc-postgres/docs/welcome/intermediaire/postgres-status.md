# État du support Alpha

Objectif : savoir ce qui fonctionne et ce qui reste à faire pour PostgreSQL.

**Ce que vous allez apprendre :** le périmètre exact du statut Alpha, pour éviter les mauvaises surprises.

Deuxième palier du **niveau intermédiaire**.

## Ce qui fonctionne

| Domaine | État |
|---|---|
| Dialecte (types, DDL) | testé unitairement |
| Traduction des paramètres `?` vers `%s` | testée unitairement |
| `db:apply` sur une base existante | fonctionnel |
| `migration:*` | fonctionnel |
| Runtime (`core.database.db`) | fonctionnel (connexion psycopg) |

## Ce qui reste

| Domaine | État |
|---|---|
| Provisioning par `db:init` | **non câblé** (base + rôle à la main) |
| Validation d'intégration sur serveur | à confirmer côté projet |
| Diff incrémental de schéma | imparfait (noms de types PostgreSQL) |

!!! warning "Préparez la base vous-même"
    Tant que `db:init` n'est pas câblé pour PostgreSQL, créez la base et le rôle avec les outils PostgreSQL.

!!! note "Contribuer"
    Valider l'intégration sur un vrai serveur (local ou Docker) et remonter les écarts aide à faire passer le backend en bêta.

## Après cette étape

[Bilan du niveau intermédiaire](bilan.md)
