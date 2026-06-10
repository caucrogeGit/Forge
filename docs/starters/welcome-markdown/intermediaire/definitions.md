# Définir des termes

**Objectif** : ajouter un petit glossaire des termes de Forge à la page.

**Ce que vous allez apprendre :** les listes de définition (extension `def_list`).

Votre page liste désormais les commandes.

Nous ajoutons un glossaire qui définit les termes clés employés dans la documentation.

## Listes de définition

Le terme est seul sur sa ligne ; chaque définition commence par deux-points et une espace.
Un terme peut recevoir plusieurs définitions.

~~~md
Contrôleur
:   Classe qui reçoit une requête et renvoie une réponse.

Route
:   Association entre un chemin d'URL et une méthode de contrôleur.
:   Peut porter un segment dynamique, par exemple `/article/{id}`.
~~~

Rendu :

Contrôleur
:   Classe qui reçoit une requête et renvoie une réponse.

Route
:   Association entre un chemin d'URL et une méthode de contrôleur.
:   Peut porter un segment dynamique, par exemple `/article/{id}`.

## Ajoutez à votre page

Ajoutez une section « Glossaire » à `prise-en-main.md` :

~~~md
## Glossaire

Module opt-in
:   Brique installable séparément, hors du noyau minimal.

Migration
:   Fichier SQL versionné qui fait évoluer le schéma de la base.
~~~

## À retenir

- Une liste de définition associe un **terme** à une ou plusieurs **définitions**.
- Le terme est seul sur sa ligne ; chaque définition commence par `:` et une espace.
- C'est plus lisible qu'un tableau pour des couples terme/explication.

[Continuer avec Mettre en avant avec les admonitions](admonitions.md)
