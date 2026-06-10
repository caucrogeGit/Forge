# Tableaux et listes de définition

**Objectif**{ .intro-label } : présenter des données tabulaires et des couples terme/définition.

**Ce que vous allez apprendre :**{ .intro-label } les tableaux (extension `tables`) avec leurs alignements, et les listes de définition (extension `def_list`).

## Tableaux

Un tableau se dessine avec des barres verticales `|` ; la deuxième ligne sépare l'en-tête du corps.

~~~md
| Colonne A | Colonne B |
|---|---|
| valeur 1 | valeur 2 |
| valeur 3 | valeur 4 |
~~~

Rendu :

| Colonne A | Colonne B |
|---|---|
| valeur 1 | valeur 2 |
| valeur 3 | valeur 4 |

## Aligner les colonnes

Les deux-points dans la ligne de séparation fixent l'alignement : à gauche, centré ou à droite.

~~~md
| Gauche | Centré | Droite |
|:---|:---:|---:|
| a | b | c |
| longue valeur | milieu | 42 |
~~~

Rendu :

| Gauche | Centré | Droite |
|:---|:---:|---:|
| a | b | c |
| longue valeur | milieu | 42 |

!!! tip "Markdown dans les cellules"
    Une cellule accepte du Markdown en ligne : `**gras**`, `` `code` ``, un [lien](bases.md) ou une icône.
    Évitez les blocs de code multi-lignes dans un tableau ; préférez alors une liste.

## Listes de définition

L'extension `def_list` associe un terme à une ou plusieurs définitions.
Le terme est seul sur sa ligne ; chaque définition commence par deux-points et une espace.

~~~md
Contrôleur
:   Classe qui reçoit une requête et renvoie une réponse.

Route
:   Association entre un chemin d'URL et une méthode de contrôleur.
:   Peut porter un segment dynamique, par exemple `/article/{id}`.
~~~

Rendu :

Contrôleur
:   Classe qui reçoit une requête et renvoie une réponse.

Route
:   Association entre un chemin d'URL et une méthode de contrôleur.
:   Peut porter un segment dynamique, par exemple `/article/{id}`.

[Continuer avec Admonitions et onglets](admonitions-et-onglets.md)
