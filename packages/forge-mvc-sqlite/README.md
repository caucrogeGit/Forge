# forge-mvc-sqlite

Backend BDD **SQLite** pour [Forge](https://forgemvc.com), au-dessus du module
`sqlite3` de la bibliothèque standard.

Depuis l'ADR-054, le cœur de Forge est agnostique BDD : il définit un contrat de
backend et découvre le backend installé via un entry point. Ce paquet fournit
l'implémentation SQLite, **sans aucune dépendance externe ni serveur**. Idéal en
développement, pour les tests et pour démarrer un projet sans installer MariaDB.

## Installation

```bash
pip install forge-mvc forge-mvc-sqlite
```

Le cœur détecte automatiquement le backend installé (entry point
`forge_mvc.db_backend`). Un seul backend BDD est autorisé par projet : n'installez
pas en même temps un autre backend (par exemple `forge-mvc-mariadb`), ou fixez
`DB_BACKEND` pour lever l'ambiguïté.

## Configuration

La base est un fichier ; son chemin est la valeur de `DB_NAME` (par exemple
`DB_NAME=app.db`). Les autres variables de connexion (`DB_HOST`, `DB_PORT`,
`DB_APP_LOGIN`, `DB_APP_PWD`) sont ignorées : SQLite n'a ni serveur ni comptes.

## Portée

Ce paquet couvre le chemin **runtime** (lecture/écriture applicative). Le SQL
généré par `make:crud` utilise des paramètres `?`, nativement supportés. La
génération de DDL et le provisioning spécifiques à SQLite relèvent de la suite
du chantier multi-SGBD (ADR-054).

## Licence

Propriétaire (voir `LICENSE`). Trajectoire MIT visée à la version 1.0.0 stable.
