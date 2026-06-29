# MariaDB (forge-mvc-mariadb)

`forge-mvc-mariadb` est le backend de base de données de production de référence de Forge, au-dessus d'un serveur MariaDB, via un pool de connexions.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.

MariaDB est client-serveur : un serveur doit être joignable.

## En bref

- backend de production par défaut, pool de connexions ;
- `db:init` provisionne base et compte (avec `DB_ADMIN_*`) ;
- deux comptes : `DB_ADMIN_*` (DDL) et `DB_APP_*` (runtime, DML) (ADR-033).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, vue d'ensemble.
- [Progression MariaDB](welcome/installation.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-mariadb
```
