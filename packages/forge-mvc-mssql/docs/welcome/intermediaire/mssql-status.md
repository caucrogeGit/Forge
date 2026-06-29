# État du support Alpha

Objectif : savoir ce qui fonctionne et ce qui reste à faire pour SQL Server.

**Ce que vous allez apprendre :** le périmètre exact du statut Alpha.

Deuxième palier du **niveau intermédiaire**.

## Ce qui fonctionne

| Domaine | État |
|---|---|
| Dialecte Transact-SQL (types, DDL) | testé unitairement |
| Paramètres `?` (pyodbc natif) | sans traduction |
| `db:apply` sur une base existante | fonctionnel |
| `migration:*` | fonctionnel |
| Runtime (`core.database.db`) | fonctionnel (connexion pyodbc) |

## Ce qui reste

| Domaine | État |
|---|---|
| Provisioning par `db:init` | **non câblé** (base + login à la main) |
| Validation d'intégration sur serveur | à confirmer côté projet |
| Diff incrémental de schéma | imparfait (noms de types SQL Server) |

!!! warning "Pilote ODBC + base à préparer"
    Vérifiez la présence d'un pilote ODBC, et créez la base et le login avec les outils SQL Server.

!!! note "Contribuer"
    Valider l'intégration sur un vrai serveur (par exemple `mcr.microsoft.com/mssql/server` en conteneur) et remonter les écarts aide à faire passer le backend en bêta.

## Après cette étape

[Bilan du niveau intermédiaire](bilan.md)
