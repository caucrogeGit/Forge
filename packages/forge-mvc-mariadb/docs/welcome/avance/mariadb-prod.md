# Vers la production

Objectif : savoir ce qui compte pour exploiter MariaDB en production avec Forge.

**Ce que vous allez apprendre :** le pool de connexions, les comptes, et l'articulation avec le déploiement.

Deuxième palier du **niveau avancé**.

## Pool de connexions

Le backend utilise un pool thread-safe : les connexions sont réutilisées entre les requêtes, ce qui convient à un serveur WSGI multi-workers (Gunicorn).

## Comptes en production

- provisionnez une fois avec `DB_ADMIN_*` (`db:init`), puis conservez ces droits hors de l'application ;
- l'application tourne avec `DB_APP_*`, limité au DML.

## Migrations en production

Appliquez les migrations de façon explicite (`forge migration:apply`) lors du déploiement, avec le compte admin, jamais automatiquement depuis une requête.

## Avec forge-mvc-deploy

L'opt-in `forge-mvc-deploy` génère `wsgi.py`, la configuration Nginx et l'unité systemd ; l'unité systemd démarre après `mariadb.service`.

!!! warning "Sauvegardes et accès"
    Mettez en place des sauvegardes du serveur MariaDB et restreignez l'accès réseau au strict nécessaire.

    Ne committez jamais `DB_*` : `env/dev` et `env/prod` sont ignorés par Git.

!!! note "Backend de production éprouvé"
    MariaDB est un backend de production mûr et complet, premier backend historique de Forge. Le cœur reste agnostique BDD (ADR-054) : le choix du backend appartient au développeur, aucun n'est imposé comme référence.

## Après cette étape

[Bilan du niveau avancé](bilan.md)
