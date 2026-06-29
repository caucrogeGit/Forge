# forge-mvc-postgres

Backend BDD **PostgreSQL** pour [Forge](https://forgemvc.com), au-dessus de
`psycopg` (v3).

Depuis l'ADR-054, le cœur de Forge est agnostique BDD : il découvre le backend
installé via un entry point. Ce paquet ajoute **PostgreSQL** à la liste des
choix de SGBD du développeur.

!!! warning "Statut Alpha"
    La logique de dialecte (types, DDL) et la traduction des paramètres
    `?` -> `%s` sont **testées unitairement**. L'**intégration avec un serveur
    PostgreSQL** et le **provisioning par la CLI** (`forge db:init`) restent à
    valider/câbler. À ce stade, créez le schéma manuellement (voir plus bas).

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
- **Insertion** : `lastrowid` via `lastval()` (séquence de session).
- **DDL** : index en instructions `CREATE INDEX` séparées (PostgreSQL n'accepte
  pas d'index dans le `CREATE TABLE`), guillemets doubles, types PostgreSQL.

## Configuration

Connexion via l'environnement (`DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_APP_LOGIN`,
`DB_APP_PWD`). Un seul backend BDD par projet : n'installez pas en même temps un
autre backend, ou fixez `DB_BACKEND`.

## Limites connues (Alpha)

- `forge db:init` ne provisionne pas encore PostgreSQL : créez la base et le
  rôle à la main (`createdb`, `CREATE ROLE`), et appliquez le SQL des entités
  généré par `make:crud` directement (`psql`).
- L'introspection de diff compare des noms de types PostgreSQL : le suivi
  incrémental de schéma peut être imparfait.

## Licence

Propriétaire (voir `LICENSE`). Trajectoire MIT visée à la version 1.0.0 stable.
