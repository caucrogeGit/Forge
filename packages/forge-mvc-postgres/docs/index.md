# PostgreSQL (forge-mvc-postgres)

`forge-mvc-postgres` est un backend de base de données pour Forge, au-dessus de `psycopg` (v3), pour faire fonctionner la couche BDD du cœur sur un serveur PostgreSQL.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.

!!! note "Niveau plein"
    Backend au niveau plein (ADR-084) : intégration validée en CI contre un vrai PostgreSQL 16.

    `forge db:init` génère le SQL de provisioning ; `forge db:init --run` l'exécute.

## En bref

- backend PostgreSQL via `psycopg` ;
- paramètres `?` de Forge traduits en `%s` ;
- identité en `BIGSERIAL` ;
- provisioning par `forge db:init` (affichage du SQL ; `--run` pour exécuter).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, statut et limites.
- [Progression PostgreSQL](welcome/debutant/postgres-welcome.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-postgres
```
