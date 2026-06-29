# Installation de forge-mvc-mariadb

Objectif : installer le backend MariaDB et préparer l'accès au serveur.

Le parcours qui suit montre, en trois niveaux, comment provisionner la base, appliquer un schéma, gérer les migrations et les comptes, puis comprendre le dialecte et la production.

## Pré-requis : un serveur MariaDB

MariaDB est client-serveur : il faut un serveur joignable (local, conteneur, ou distant).

Le paquet `mariadb` (pilote) est installé avec l'opt-in.

## Installer le paquet

```bash
pip install --pre forge-mvc-mariadb
```

## Configurer l'environnement

Dans `env/dev`, renseignez les accès (le squelette ne les pré-câble pas) :

```env
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=mon_projet
DB_APP_LOGIN=mon_projet
DB_APP_PWD=...
DB_ADMIN_LOGIN=root
DB_ADMIN_PWD=...
```

`DB_ADMIN_*` sert au provisioning et à la DDL ; `DB_APP_*` au runtime.

## Vérifier

```bash
forge doctor
```

`doctor` indique le backend résolu (`mariadb`) et l'état de la connexion.

!!! note "Un seul backend par projet"
    Si un autre backend est installé, fixez `DB_BACKEND=mariadb`.

## Après cette étape

[Niveau débutant : Provisionner la base](debutant/mariadb-welcome.md)
