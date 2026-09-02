# pyright: strict
"""Rognage autour d'un point d'intérêt (`IMAGES-FOCAL-CROP-001`).

Une variante en mode `crop` remplit exactement sa boîte, ce qu'un rognage
centré fait mal : sur une photo de groupe cadrée large, le centre géométrique
tombe souvent entre deux personnes, et une bannière de 1920 sur 1080 taillée
dans un portrait vertical coupe la tête.

Le point d'intérêt dit quelle partie de l'image doit survivre au rognage. Il
est exprimé en fractions de la largeur et de la hauteur, de sorte qu'il reste
valable quelles que soient les dimensions de la source et de la cible.

`FocalPoint(0.5, 0.5)` est le centre, et c'est ce qui s'applique par défaut :
le mode `crop` sans point d'intérêt se comporte comme un rognage centré.

## Ce que Forge ne fait pas

Il ne **détecte** aucun point d'intérêt.

La détection de visages ou de saillance demande un modèle, donc une dépendance
lourde et des résultats à surveiller. Le point est une donnée de l'application,
posée par la personne qui téléverse ou par un service qu'elle choisit.

Forge n'**invente** pas non plus de pixels. Si la source est plus petite que la
boîte demandée, la variante garde le rapport de la boîte mais reste à la taille
disponible : agrandir produirait une image floue en se faisant passer pour la
taille déclarée.
"""
from __future__ import annotations

from dataclasses import dataclass

from PIL import Image

__all__ = ["FocalPoint", "CENTER", "crop_box", "crop_to_focal"]


@dataclass(frozen=True)
class FocalPoint:
    """Point à préserver, en fractions de la largeur et de la hauteur.

    `(0, 0)` est le coin supérieur gauche, `(1, 1)` le coin inférieur droit.

    Les valeurs hors de l'intervalle sont **ramenées** dedans plutôt que
    refusées : un point d'intérêt vient souvent d'une interface de saisie, et
    un clic au bord donne facilement `1.0001`. Refuser ferait échouer un
    téléversement pour un arrondi.
    """

    x: float = 0.5
    y: float = 0.5

    def __post_init__(self) -> None:
        object.__setattr__(self, "x", min(1.0, max(0.0, float(self.x))))
        object.__setattr__(self, "y", min(1.0, max(0.0, float(self.y))))


#: Point par défaut. Le mode `crop` sans point d'intérêt rogne au centre.
CENTER = FocalPoint(0.5, 0.5)


def crop_box(
    source: "tuple[int, int]",
    target: "tuple[int, int]",
    focal: "FocalPoint | None" = None,
) -> "tuple[int, int, int, int]":
    """Fenêtre à découper dans la source, au rapport de la cible.

    La fenêtre est la plus grande possible au rapport demandé, centrée sur le
    point d'intérêt, puis **ramenée dans l'image**. Sans ce recalage, un point
    proche d'un bord donnerait une fenêtre à cheval sur le vide, et Pillow
    comblerait la partie manquante par du noir.

    Rend un quadruplet `(gauche, haut, droite, bas)`.
    """
    largeur_source, hauteur_source = source
    largeur_cible, hauteur_cible = target
    if largeur_source <= 0 or hauteur_source <= 0:
        raise ValueError(f"Dimensions source invalides : {source}.")
    if largeur_cible <= 0 or hauteur_cible <= 0:
        raise ValueError(f"Dimensions cible invalides : {target}.")

    point = focal or CENTER
    rapport_cible = largeur_cible / hauteur_cible

    # La plus grande fenêtre au rapport cible qui tient dans la source.
    if largeur_source / hauteur_source > rapport_cible:
        hauteur_fenetre = hauteur_source
        largeur_fenetre = int(round(hauteur_source * rapport_cible))
    else:
        largeur_fenetre = largeur_source
        hauteur_fenetre = int(round(largeur_source / rapport_cible))

    largeur_fenetre = max(1, min(largeur_fenetre, largeur_source))
    hauteur_fenetre = max(1, min(hauteur_fenetre, hauteur_source))

    centre_x = point.x * largeur_source
    centre_y = point.y * hauteur_source
    gauche = int(round(centre_x - largeur_fenetre / 2))
    haut = int(round(centre_y - hauteur_fenetre / 2))

    # Recalage dans l'image : le point d'intérêt reste au plus près du centre
    # de la fenêtre sans que celle ci déborde.
    gauche = max(0, min(gauche, largeur_source - largeur_fenetre))
    haut = max(0, min(haut, hauteur_source - hauteur_fenetre))

    return (gauche, haut, gauche + largeur_fenetre, haut + hauteur_fenetre)


def crop_to_focal(
    image: Image.Image,
    target: "tuple[int, int]",
    focal: "FocalPoint | None" = None,
) -> Image.Image:
    """Rogne puis met à l'échelle pour remplir exactement la boîte.

    Si la fenêtre découpée est plus petite que la boîte, elle est **conservée
    telle quelle** : agrandir produirait une image floue se faisant passer pour
    la taille déclarée. La variante garde alors le rapport demandé, à la taille
    disponible.
    """
    fenetre = crop_box(image.size, target, focal)
    rognee = image.crop(fenetre)

    largeur_cible, hauteur_cible = target
    if rognee.width <= largeur_cible and rognee.height <= hauteur_cible:
        return rognee
    # Les stubs Pillow ne typent pas complètement `resize`, contrairement à
    # `crop` juste au dessus ; la valeur rendue est bien une image.
    return rognee.resize(  # pyright: ignore[reportUnknownMemberType]
        (largeur_cible, hauteur_cible), Image.Resampling.LANCZOS
    )
