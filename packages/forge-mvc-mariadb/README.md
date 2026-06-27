# forge-mvc-mariadb

Backend BDD **MariaDB** pour [Forge](https://forgemvc.com).

Depuis l'ADR-054, le cœur de Forge est agnostique BDD : il définit un contrat
de backend et découvre le backend installé via un entry point. Ce paquet fournit
l'implémentation MariaDB (pool de connexions).

## Installation

```bash
pip install forge-mvc forge-mvc-mariadb
```

Le cœur détecte automatiquement le backend installé (entry point
`forge_mvc.db_backend`) : aucune configuration de câblage n'est nécessaire.
Un seul backend BDD est autorisé par projet.

## Dépendance système

Le connecteur `mariadb` requiert la bibliothèque cliente MariaDB
(`libmariadb-dev` sur Debian/Ubuntu).

## Configuration

La connexion se règle via l'environnement, comme avant (`DB_HOST`, `DB_PORT`,
`DB_NAME`, `DB_APP_LOGIN`, `DB_APP_PWD`, `DB_POOL_SIZE`).

## Licence

Propriétaire (voir `LICENSE`). Trajectoire MIT visée à la version 1.0.0 stable.
