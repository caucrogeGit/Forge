# Quand choisir SQLite

Objectif : savoir quand SQLite est le bon backend, et quand passer à un serveur.

**Ce que vous allez apprendre :** SQLite est excellent pour démarrer ; un backend serveur devient utile à l'échelle.

Deuxième palier du **niveau avancé**.

## SQLite brille pour

- le **développement** : zéro installation, une base = un fichier ;
- les **tests** : base jetable, rapide, isolée ;
- l'**onboarding** : un nouveau contributeur démarre en une commande ;
- les petites applications mono-processus.

## Préférez un backend serveur pour

- la **production multi-utilisateurs** : MariaDB ou PostgreSQL gèrent mieux la concurrence en écriture ;
- les déploiements **multi-process** (plusieurs workers Gunicorn écrivant beaucoup) ;
- les besoins de droits, de réplication ou d'outillage serveur.

## Changer de backend

Le cœur étant agnostique (ADR-054), passer de SQLite à un serveur consiste à installer l'autre backend et à fixer `DB_BACKEND` : le code applicatif ne change pas (le SQL reste natif, assumé).

!!! note "Un seul backend par projet"
    Vous n'installez qu'un backend BDD à la fois.

    Le SQL applicatif est natif du SGBD choisi : Forge ne promet pas une portabilité automatique, il garde le SQL visible.

## Après cette étape

[Bilan du niveau avancé](bilan.md)
