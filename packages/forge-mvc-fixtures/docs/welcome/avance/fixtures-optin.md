# Un opt-in CLI-only

Objectif : comprendre pourquoi les fixtures sont un opt-in séparé, à ligne de commande seule.

**Ce que vous allez apprendre :** peupler une base de démo est de l'outillage de développement, pas du runtime de framework.

## Pourquoi un opt-in

Le cœur de Forge reste minimal (principe 8) : il ne porte que le runtime nécessaire à servir des requêtes.
Charger des données de démonstration n'en fait pas partie.
La question d'un `forge db:seed` dans le cœur avait d'ailleurs été écartée comme hors périmètre.

Les fixtures rejoignent donc les briques optionnelles, installées à la demande.
Une application qui n'en a pas besoin ne l'installe pas.

## CLI seule

`forge-mvc-fixtures` n'expose **aucune API runtime** : votre application ne l'importe jamais à l'exécution.
Il n'ajoute que deux commandes, découvertes par le cœur quand le paquet est installé.

C'est le même profil que `forge-mvc-deploy` : de l'outillage, invoqué explicitement, jamais dans le chemin d'une requête.

## SQL visible, rien de caché

Les fixtures sont des `.sql` que vous relisez.
Les commandes **affichent** le SQL avant de l'exécuter (charte §7 et principe 3).
La purge **montre** les `DELETE` qu'elle dérive de vos fixtures avant de les lancer.

À aucun moment Forge n'écrit dans votre base sans que vous ayez vu quoi.

## Indépendance

L'opt-in dépend du cœur, jamais l'inverse : le cœur ne connaît pas `forge-mvc-fixtures`.
Vous pouvez le désinstaller sans rien casser dans le cœur.

## La suite

Faisons le bilan du niveau avancé.

[Suivant : scénarios et instantanés](fixtures-scenarios-snapshot.md)
