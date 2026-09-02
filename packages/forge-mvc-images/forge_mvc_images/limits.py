# pyright: strict
"""Limites de dimensions et de poids, déclarées (`IMAGES-LIMITS-CONFIG-001`).

Le paquet portait une seule limite, la surface en pixels, pensée contre la
bombe de décompression. Elle laisse passer une image de 12000 sur 2000, qui
tient sous les 24 mégapixels et qui est pourtant impossible à afficher, coûteuse
à redimensionner et volumineuse à servir.

Trois limites manquaient donc, et une application n'avait aucun moyen de les
poser sans écrire son propre contrôle.

| Variable | Ce qu'elle borne |
|---|---|
| `IMAGE_MAX_WIDTH` | largeur en pixels |
| `IMAGE_MAX_HEIGHT` | hauteur en pixels |
| `IMAGE_MAX_BYTES` | poids du fichier image |
| `UPLOAD_MAX_IMAGE_PIXELS` | surface, garde anti bombe, déjà présente |

Sans déclaration, aucune de ces trois n'est appliquée. Le contrôle de surface
reste en place, il protégeait contre autre chose.

## Une valeur illisible interrompt

Comme pour le quota de `forge-mvc-files`, une valeur illisible **lève** au lieu
d'être ignorée. Retomber en silence sur « aucune limite » à cause d'une faute de
frappe irait exactement dans le mauvais sens.
"""
from __future__ import annotations

import os
from dataclasses import dataclass

from core.forms.upload_exceptions import UploadStorageError

__all__ = [
    "ImageLimitsError",
    "ImageLimits",
    "ENV_MAX_WIDTH",
    "ENV_MAX_HEIGHT",
    "ENV_MAX_BYTES",
    "ENV_MAX_PIXELS",
    "DEFAULT_MAX_PIXELS",
    "image_limits",
    "check_dimensions",
    "check_weight",
]

ENV_MAX_WIDTH = "IMAGE_MAX_WIDTH"
ENV_MAX_HEIGHT = "IMAGE_MAX_HEIGHT"
ENV_MAX_BYTES = "IMAGE_MAX_BYTES"
ENV_MAX_PIXELS = "UPLOAD_MAX_IMAGE_PIXELS"

#: Surface maximale par défaut, garde anti bombe de décompression.
DEFAULT_MAX_PIXELS = 24_000_000


class ImageLimitsError(ValueError):
    """Limite mal déclarée dans l'environnement."""


@dataclass(frozen=True)
class ImageLimits:
    """Bornes applicables à une image. `None` veut dire « non bornée »."""

    max_width: "int | None" = None
    max_height: "int | None" = None
    max_bytes: "int | None" = None
    max_pixels: int = DEFAULT_MAX_PIXELS


def _lire(nom: str, defaut: "int | None" = None) -> "int | None":
    brut = (os.getenv(nom) or "").strip()
    if not brut:
        return defaut
    try:
        valeur = int(brut)
    except ValueError:
        raise ImageLimitsError(
            f"{nom} doit être un entier. Reçu : {brut!r}. Les suffixes comme "
            "« 5MB » ne sont pas lus, écrire le nombre en clair."
        ) from None
    if valeur <= 0:
        raise ImageLimitsError(
            f"{nom} doit être strictement positif. Reçu : {valeur}. "
            "Pour ne pas borner, retirer la variable."
        )
    return valeur


def image_limits() -> ImageLimits:
    """Limites applicables, lues de l'environnement à chaque appel.

    Raises:
        ImageLimitsError: une valeur est illisible ou nulle.
    """
    surface = _lire(ENV_MAX_PIXELS, DEFAULT_MAX_PIXELS)
    return ImageLimits(
        max_width=_lire(ENV_MAX_WIDTH),
        max_height=_lire(ENV_MAX_HEIGHT),
        max_bytes=_lire(ENV_MAX_BYTES),
        max_pixels=surface if surface is not None else DEFAULT_MAX_PIXELS,
    )


def check_dimensions(
    width: int, height: int, *, limits: "ImageLimits | None" = None
) -> None:
    """Refuse une image trop large, trop haute, ou de surface démesurée.

    Le contrôle porte sur les dimensions lues dans l'en tête, avant tout
    décodage : refuser après aurait déjà coûté la mémoire qu'on voulait éviter.

    Raises:
        UploadStorageError: une borne est franchie. Le type est celui des
            autres refus d'upload, de sorte qu'un contrôleur qui les traite
            déjà traite aussi ceux ci.
    """
    bornes = limits if limits is not None else image_limits()

    if width * height > bornes.max_pixels:
        raise UploadStorageError(
            f"Image trop volumineuse ({width}×{height} pixels) ; "
            f"plafond autorisé : {bornes.max_pixels} pixels."
        )
    if bornes.max_width is not None and width > bornes.max_width:
        raise UploadStorageError(
            f"Image trop large ({width} pixels) ; "
            f"largeur maximale autorisée : {bornes.max_width}."
        )
    if bornes.max_height is not None and height > bornes.max_height:
        raise UploadStorageError(
            f"Image trop haute ({height} pixels) ; "
            f"hauteur maximale autorisée : {bornes.max_height}."
        )


def check_weight(size_bytes: int, *, limits: "ImageLimits | None" = None) -> None:
    """Refuse un fichier image trop lourd.

    Distinct d'`upload_max_size`, qui borne **tout** envoi. Une application peut
    accepter un PDF de 20 Mo et refuser une photo de 5 Mo, les deux n'ayant ni
    le même usage ni le même coût de traitement.

    Raises:
        UploadStorageError: le poids dépasse `IMAGE_MAX_BYTES`.
    """
    bornes = limits if limits is not None else image_limits()
    if bornes.max_bytes is not None and size_bytes > bornes.max_bytes:
        raise UploadStorageError(
            f"Image trop lourde ({size_bytes} octets) ; "
            f"poids maximal autorisé : {bornes.max_bytes} octets."
        )
