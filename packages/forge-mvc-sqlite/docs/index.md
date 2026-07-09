# SQLite (forge-mvc-sqlite)

`forge-mvc-sqlite` est un backend de base de données pour Forge, au-dessus de `sqlite3` (bibliothèque standard), sans serveur ni dépendance externe.

Le cœur de Forge est agnostique BDD (ADR-054) : il découvre le backend installé et n'en utilise qu'un seul par projet.

SQLite range toute la base dans un fichier : c'est le choix le plus simple pour démarrer, développer et tester.

## En bref

- une base = un fichier (`DB_NAME`), aucun serveur à installer ;
- découvert automatiquement par le cœur dès qu'il est installé ;
- on l'utilise via les commandes du cœur (`db:init`, `db:apply`, `migration:*`).

## Par où commencer

- [Référence](reference.md) : rôle, contrat, dialecte, vue d'ensemble.
- [Progression SQLite](welcome/debutant/sqlite-welcome.md) : apprendre le backend pas à pas.

## Installation

```bash
pip install --pre forge-mvc-sqlite
```
