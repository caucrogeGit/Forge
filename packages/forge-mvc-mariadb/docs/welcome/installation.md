# Installation de forge-mvc-mariadb

Objectif : installer le backend MariaDB et préparer l'accès au serveur avant d'entamer le parcours.

Le parcours qui suit montre, en trois niveaux, comment provisionner la base, appliquer un schéma, gérer les migrations et les comptes, puis comprendre le dialecte et la production.

## La procédure d'installation

La procédure d'installation est décrite, pas à pas, dans la référence du backend, chapitre « 2. Installation et désinstallation ».
Elle couvre les cinq étapes : installer le paquet (PyPI ou Git), amorcer l'environnement avec `forge db:config`, renseigner les accès dans `env/dev`, vérifier avec `forge doctor`, puis provisionner avec `forge db:init`.

[Référence du backend MariaDB](../reference.md)

Suivez ces cinq étapes, puis revenez ici pour la suite du parcours.

!!! note "Un seul backend par projet"
    MariaDB est client-serveur : prévoyez un serveur joignable (local, conteneur ou distant).
    Si un autre backend est installé, fixez `DB_BACKEND=mariadb`.

## Après cette étape

[Niveau débutant : Provisionner la base](debutant/mariadb-welcome.md)
