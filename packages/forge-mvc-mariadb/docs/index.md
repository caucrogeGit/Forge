# MariaDB (forge-mvc-mariadb)

`forge-mvc-mariadb` est un backend de base de données de production pour Forge, au-dessus d'un serveur MariaDB, via un pool de connexions.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet, au choix du développeur (MariaDB, SQLite, PostgreSQL ou SQL Server).

MariaDB est client-serveur : un serveur doit être joignable.

## En bref

- backend de production, client-serveur, pool de connexions ;
- `db:init` provisionne base et compte (avec `DB_ADMIN_*`) ;
- deux comptes : `DB_ADMIN_*` (DDL) et `DB_APP_*` (runtime, DML) (ADR-033).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, vue d'ensemble.
- [Progression MariaDB](welcome/installation.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-mariadb
```
