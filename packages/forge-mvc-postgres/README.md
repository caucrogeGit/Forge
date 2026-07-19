# forge-mvc-postgres

Backend BDD **PostgreSQL** pour [Forge](https://forgemvc.com), au-dessus de
`psycopg` (v3).

Depuis l'ADR-054, le cœur de Forge est agnostique BDD : il découvre le backend
installé via un entry point. Ce paquet ajoute **PostgreSQL** à la liste des
choix de SGBD du développeur.

!!! note "Niveau plein"
    Backend au **niveau plein** (ADR-084, révision du 2026-07-19).
    L'intégration est validée en CI contre un vrai PostgreSQL 16 (couche BDD et runner de migrations).
    `forge db:init` génère le SQL de provisioning ; `forge db:init --run` l'exécute.

## Installation

```bash
pip install forge-mvc forge-mvc-postgres
```

PostgreSQL est **client-serveur** : un serveur PostgreSQL doit être joignable
(installé localement, en conteneur `docker run ... postgres`, ou distant).
`psycopg` n'est que le client.

## Particularités gérées

- **Paramètres** : Forge génère du SQL avec `?` ; l'adaptateur traduit en `%s`
  (format psycopg) à l'exécution, en préservant les littéraux chaîne.
- **Identité** : clé primaire auto-incrémentée en `BIGSERIAL`.
- **Insertion** : `lastrowid` fiable via `lastval()` sous garde savepoint
  (`PG-INSERT-IDENTITY-001`).
- **DDL** : index en instructions `CREATE INDEX` séparées (PostgreSQL n'accepte
  pas d'index dans le `CREATE TABLE`), guillemets doubles, types PostgreSQL.

## Configuration

Connexion via l'environnement (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`,
`DB_APP_PWD`). Un seul backend BDD par projet : n'installez pas en même temps un
autre backend, ou fixez `DB_BACKEND`.

## Provisioning

`forge db:init` génère et affiche le SQL de provisioning PostgreSQL
(rôles admin et applicatif, base, GRANT, `ALTER DEFAULT PRIVILEGES`,
table `forge_migrations`).
`forge db:init --run` l'exécute : le compte `DB_ADMIN_*` doit exister ;
`--run` crée la base, le rôle applicatif et le registre de migrations.

## Limites connues

- L'escape hatch `DB_APP_PRIVILEGES` au-delà du DML (SELECT, INSERT, UPDATE,
  DELETE) reste propre à MariaDB : refus explicite sur PostgreSQL.
- L'introspection de diff compare des noms de types PostgreSQL : le suivi
  incrémental de schéma peut être imparfait.

## Licence

Propriétaire (voir `LICENSE`). Trajectoire MIT visée à la version 1.0.0 stable.
