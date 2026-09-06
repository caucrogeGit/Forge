# Intermédiaire 5 : Le recadrage focal

Objectif : qu'un portrait recadré en carré garde le visage, pas le plafond.

## Ce que `crop` coupe sans le savoir

Un recadrage centré prend le milieu géométrique de l'image.
Sur une photo de groupe où quelqu'un est à gauche, le milieu est un mur.

Un **point focal** dit quel endroit doit rester visible.

```python
from forge_mvc_images import FocalPoint, crop_to_focal

recadree = crop_to_focal(image, (300, 300), FocalPoint(x=0.3, y=0.25))
```

Les coordonnées sont **relatives**, entre 0 et 1 : `0.5, 0.5` est le centre, `0, 0` le coin haut gauche.

!!! info "Relatives, donc valables à toutes les tailles"
    Un point en pixels serait faux dès que l'original change de taille, ou qu'une variante plus petite est recadrée à son tour.

!!! warning "Le point est une préférence, pas une garantie"
    Si la boîte demandée est plus grande que ce que l'image permet autour du point, le recadrage se décale pour rester dans l'image.

    Mieux vaut un cadrage un peu décalé qu'une bande vide sur le côté.

!!! danger "Sans point focal, le comportement ne change pas"
    `crop_to_focal(image, cible)` sans point recadre au centre, comme avant.

    Ajouter cette fonction ne modifie donc aucune image déjà produite.

## À retenir

- Le point focal est relatif, entre 0 et 1, et vaut pour toutes les tailles.
- Il oriente le recadrage sans jamais sortir de l'image.
- Sans lui, le centre reste le comportement.

## Étape suivante

[Bilan du niveau intermédiaire](bilan.md)
