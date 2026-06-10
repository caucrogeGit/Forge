# Titre et introduction

**Objectif** : poser le squelette de la page « Prise en main de Forge » avec un titre et une introduction.

**Ce que vous allez apprendre :** les titres (`#`), les paragraphes, la convention « une phrase par ligne » et l'échappement des caractères.

!!! info "Le fil rouge"
    Vous créez maintenant le fichier `prise-en-main.md`.
    Tout au long du parcours, vous y ajouterez des sections.
    Ce premier palier en pose le titre et l'introduction.

## Les titres

Un titre commence par un à six `#`, suivis d'une espace.
Le niveau 1 est réservé au **titre de la page** : un seul par fichier.

~~~md
# Prise en main de Forge
## Présentation
### Pour qui ?
~~~

Les titres de niveau 2 et 3 alimentent le sommaire de droite, chacun avec une ancre cliquable.

## Les paragraphes

Une ligne vide sépare deux paragraphes.
Dans la source, on écrit **une phrase par ligne** : le rendu regroupe les lignes d'un même paragraphe, mais les différences de version restent lisibles.

~~~md
Forge est un framework web Python.
Il est explicite, pédagogique et testable.
~~~

Rendu :

Forge est un framework web Python.
Il est explicite, pédagogique et testable.

## Échapper un caractère

Pour afficher un caractère spécial littéralement, précédez-le d'un antislash.

~~~md
Le dossier \*spécial\* n'est pas en italique.
~~~

Rendu :

Le dossier \*spécial\* n'est pas en italique.

## Ajoutez à votre page

Créez le fichier `prise-en-main.md` avec ce contenu de départ :

~~~md
# Prise en main de Forge

Forge est un framework web Python explicite, pédagogique et testable.
Cette page vous guide pour installer Forge et créer votre premier projet.

## Présentation
~~~

## À retenir

- Un seul titre de niveau 1 par page : c'est le titre du document.
- Une ligne vide sépare les paragraphes ; on écrit une phrase par ligne.
- L'antislash échappe un caractère spécial.

[Continuer avec La mise en forme du texte](mise-en-forme.md)
