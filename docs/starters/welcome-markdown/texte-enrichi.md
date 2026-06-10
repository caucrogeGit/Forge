# Texte enrichi

**Objectif**{ .intro-label } : enrichir le texte avec du surlignage, des exposants, des touches clavier, des symboles et des émojis.

**Ce que vous allez apprendre :**{ .intro-label } les extensions `mark`, `caret`, `tilde`, `keys`, `smartsymbols`, `emoji` et `progressbar`.

## Surligner

L'extension `mark` surligne entre doubles `==`.

~~~md
Une notion ==vraiment importante== à retenir.
~~~

Rendu :

Une notion ==vraiment importante== à retenir.

## Exposant et insertion

L'extension `caret` produit l'exposant entre `^` simples et le texte « inséré » (souligné) entre `^^` doubles.

~~~md
La surface vaut 5 m^2^.
Une correction ^^ajoutée^^ au texte.
~~~

Rendu :

La surface vaut 5 m^2^.
Une correction ^^ajoutée^^ au texte.

## Indice et barré

L'extension `tilde` produit l'indice entre `~` simples et le texte barré entre `~~` doubles.

~~~md
La formule de l'eau est H~2~O.
Un prix ~~barré~~ remplacé.
~~~

Rendu :

La formule de l'eau est H~2~O.
Un prix ~~barré~~ remplacé.

## Touches clavier

L'extension `keys` transforme `++touche+touche++` en vraies touches stylées.

~~~md
Copier avec ++ctrl+c++, coller avec ++ctrl+v++.
Forcer l'arrêt avec ++ctrl+alt+delete++.
~~~

Rendu :

Copier avec ++ctrl+c++, coller avec ++ctrl+v++.
Forcer l'arrêt avec ++ctrl+alt+delete++.

## Symboles typographiques

L'extension `smartsymbols` convertit certaines suites de caractères en symboles.

~~~md
Copyright (c), marque (tm), marque déposée (r).
Tolérance +/- 2 %, ensemble 1/2 et 1/4.
Flèches : --> et <-- et <-->.
~~~

Rendu :

Copyright (c), marque (tm), marque déposée (r).
Tolérance +/- 2 %, ensemble 1/2 et 1/4.
Flèches : --> et <-- et <-->.

## Émojis et icônes

L'extension `emoji`, câblée sur le jeu d'icônes Material, accepte les codes `:nom:`.

~~~md
Validé :material-check: ou en alerte :material-alert:.
Une icône de fusée :material-rocket-launch: et un émoji :smile:.
~~~

Rendu :

Validé :material-check: ou en alerte :material-alert:.
Une icône de fusée :material-rocket-launch: et un émoji :smile:.

## Barres de progression

L'extension `progressbar` dessine une jauge avec `[=pourcentage "libellé"]`.

~~~md
[=30% "30 %"]
[=85% "85 %"]
[=100% "Terminé"]
~~~

Rendu :

[=30% "30 %"]
[=85% "85 %"]
[=100% "Terminé"]

[Continuer avec Notes, abréviations et attributs](notes-abreviations-attributs.md)
