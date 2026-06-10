# La mise en forme du texte

**Objectif** : enrichir la présentation de Forge avec de l'emphase et du code en ligne.

**Ce que vous allez apprendre :** le gras, l'italique (extension `betterem`), le code en ligne et le code en ligne coloré (extension `inlinehilite`).

Votre page possède un titre, une introduction et un titre « Présentation ».

Nous remplissons cette section en mettant en valeur les mots importants.

## Gras et italique

L'extension `betterem` gère finement les marqueurs.

~~~md
Forge garde le **SQL visible** et refuse la _magie cachée_.
On peut **_combiner_** les deux.
~~~

Rendu :

Forge garde le **SQL visible** et refuse la _magie cachée_.
On peut **_combiner_** les deux.

## Code en ligne

Entourez un fragment de simples accents graves : il s'affiche en police à chasse fixe.

~~~md
Installez Forge avec `pip`, puis lancez `forge serve`.
~~~

Rendu :

Installez Forge avec `pip`, puis lancez `forge serve`.

## Code en ligne coloré

Avec `inlinehilite`, un préfixe `#!langage` colore même le code en ligne.

~~~md
Un appel Python en ligne : `#!python Response.text("Bonjour")`.
~~~

Rendu :

Un appel Python en ligne : `#!python Response.text("Bonjour")`.

## Ajoutez à votre page

Complétez la section « Présentation » de `prise-en-main.md` :

~~~md
## Présentation

Forge est **explicite** : le `SQL` reste visible et il n'y a pas de _magie cachée_.
Le noyau est **minimal** ; les fonctions avancées s'ajoutent en modules opt-in.
~~~

## À retenir

- `**gras**`, `_italique_`, et `**_les deux_**`.
- Le code en ligne se met entre accents graves : `` `comme ceci` ``.
- `inlinehilite` colore le code en ligne avec le préfixe `#!langage`.

[Continuer avec Les listes](listes.md)
