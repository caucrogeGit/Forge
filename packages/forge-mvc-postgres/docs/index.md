# PostgreSQL (forge-mvc-postgres)

`forge-mvc-postgres` est un backend de base de données pour Forge, au-dessus de `psycopg` (v3), pour faire fonctionner la couche BDD du cœur sur un serveur PostgreSQL.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.

!!! warning "Statut Alpha"
    Dialecte et traduction des paramètres testés unitairement ; intégration serveur et provisioning CLI à valider/câbler.

    Créez la base et le rôle à la main, puis utilisez `db:apply` / `migration:*`.

## En bref

- backend PostgreSQL via `psycopg` ;
- paramètres `?` de Forge traduits en `%s` ;
- identité en `BIGSERIAL` ;
- provisioning CLI pas encore câblé (création base + rôle manuelle).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, statut Alpha.
- [Progression PostgreSQL](welcome/debutant/postgres-welcome.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-postgres
```
