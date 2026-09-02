# pyright: strict
"""Préréglages de variantes déclarés par configuration (`IMAGES-PRESETS-DECLARATIFS-001`).

Les deux variantes du paquet, `medium` et `thumbnail`, vivaient dans une
constante de module et dans deux dictionnaires littéraux qui devaient s'accorder
avec elle. Ajouter une taille demandait donc d'éditer le paquet en trois
endroits, et l'ADR-018 avait relevé la conséquence sans la corriger.

Une application a pourtant des besoins que Forge ne peut pas deviner : une
bannière large, un carré pour un avatar, une image sociale de 1200 sur 630.

## Ce que le module change

Les préréglages sont **lus**, jamais figés à l'import. La constante précédente
était un instantané pris au chargement du module, ce qui la rendait aveugle à
toute configuration posée ensuite.

## Format

    IMAGE_VARIANTS=thumbnail:300x300,medium:1280x1280,hero:1920x1080:crop

Chaque entrée porte un nom, des dimensions, et un mode facultatif. Sans
déclaration, les deux préréglages historiques s'appliquent, un projet existant
ne changeant donc pas de comportement.
"""
from __future__ import annotations

import os
import re
from dataclasses import dataclass

__all__ = [
    "ImagePresetError",
    "VariantPreset",
    "DEFAULT_PRESETS",
    "RESERVED_PRESET_NAMES",
    "PRESET_NAME_RE",
    "MODE_FIT",
    "MODE_CROP",
    "ENV_VARIANTS",
    "variant_presets",
    "preset_by_name",
    "preset_names",
    "parse_presets",
]

#: Garde le rapport largeur sur hauteur, l'image tient dans la boîte.
MODE_FIT = "fit"
#: Remplit la boîte exactement, en rognant le débord.
MODE_CROP = "crop"

_MODES = {MODE_FIT, MODE_CROP}

#: Le nom devient un segment de chemin sur le disque. Public : le nettoyage
#: des variantes (`IMAGES-ORPHAN-VARIANTS-001`) reconnaît un dossier avec.
PRESET_NAME_RE = re.compile(r"^[a-z0-9][a-z0-9_-]*$")

#: `original` désigne le fichier source dans tous les dictionnaires de chemins.
RESERVED_PRESET_NAMES = frozenset({"original"})

ENV_VARIANTS = "IMAGE_VARIANTS"

#: Plafond par dimension. Au delà, la variante pèserait plus que l'original.
_MAX_DIMENSION = 20_000


class ImagePresetError(ValueError):
    """Préréglage mal déclaré."""


@dataclass(frozen=True)
class VariantPreset:
    """Une déclinaison à produire pour chaque image.

    Immuable : les préréglages sont lus une fois par appel et traversent la
    génération, où une modification en cours de route donnerait deux variantes
    de tailles différentes sous le même nom.
    """

    name: str
    width: int
    height: int
    mode: str = MODE_FIT

    @property
    def size(self) -> "tuple[int, int]":
        return (self.width, self.height)

    @property
    def crops(self) -> bool:
        return self.mode == MODE_CROP


#: Préréglages appliqués quand rien n'est déclaré. Ceux du paquet avant le ticket.
DEFAULT_PRESETS: "tuple[VariantPreset, ...]" = (
    VariantPreset("medium", 1280, 1280),
    VariantPreset("thumbnail", 300, 300),
)


def _lire_dimension(brut: str, entree: str) -> int:
    try:
        valeur = int(brut)
    except ValueError:
        raise ImagePresetError(
            f"Dimension illisible dans {entree!r} : {brut!r} n'est pas un entier."
        ) from None
    if valeur <= 0:
        raise ImagePresetError(
            f"Dimension nulle ou négative dans {entree!r} : {valeur}."
        )
    if valeur > _MAX_DIMENSION:
        raise ImagePresetError(
            f"Dimension démesurée dans {entree!r} : {valeur} dépasse {_MAX_DIMENSION}."
        )
    return valeur


def _lire_entree(entree: str) -> VariantPreset:
    morceaux = entree.split(":")
    if len(morceaux) not in (2, 3):
        raise ImagePresetError(
            f"Entrée mal formée : {entree!r}. Attendu « nom:LARGEURxHAUTEUR » "
            "ou « nom:LARGEURxHAUTEUR:mode »."
        )

    nom = morceaux[0].strip().lower()
    if not PRESET_NAME_RE.fullmatch(nom):
        raise ImagePresetError(
            f"Nom de préréglage invalide : {nom!r}. Le nom devient un dossier "
            "sur le disque, il doit être en minuscules, chiffres, tiret ou "
            "souligné, et commencer par une lettre ou un chiffre."
        )
    if nom in RESERVED_PRESET_NAMES:
        raise ImagePresetError(
            f"Nom de préréglage réservé : {nom!r}. Il désigne le fichier source, "
            "et une variante portant ce nom l'écraserait."
        )

    dimensions = morceaux[1].strip().lower().split("x")
    if len(dimensions) != 2:
        raise ImagePresetError(
            f"Dimensions mal formées dans {entree!r}. Attendu « LARGEURxHAUTEUR »."
        )
    largeur = _lire_dimension(dimensions[0].strip(), entree)
    hauteur = _lire_dimension(dimensions[1].strip(), entree)

    mode = morceaux[2].strip().lower() if len(morceaux) == 3 else MODE_FIT
    if mode not in _MODES:
        raise ImagePresetError(
            f"Mode inconnu dans {entree!r} : {mode!r}. "
            f"Attendu {MODE_FIT!r} ou {MODE_CROP!r}."
        )

    return VariantPreset(nom, largeur, hauteur, mode)


def parse_presets(declaration: str) -> "tuple[VariantPreset, ...]":
    """Lit une déclaration. Rend les préréglages par défaut si elle est vide.

    Raises:
        ImagePresetError: entrée mal formée, nom invalide ou réservé, dimension
            illisible, mode inconnu, ou deux préréglages du même nom.
    """
    texte = (declaration or "").strip()
    if not texte:
        return DEFAULT_PRESETS

    presets: list[VariantPreset] = []
    vus: set[str] = set()
    for morceau in texte.split(","):
        entree = morceau.strip()
        if not entree:
            continue
        preset = _lire_entree(entree)
        if preset.name in vus:
            raise ImagePresetError(
                f"Préréglage déclaré deux fois : {preset.name!r}. Garder la "
                "dernière déclaration en silence produirait une taille que "
                "personne n'a lue."
            )
        vus.add(preset.name)
        presets.append(preset)

    if not presets:
        return DEFAULT_PRESETS
    return tuple(presets)


def variant_presets() -> "tuple[VariantPreset, ...]":
    """Préréglages applicables, lus de l'environnement à chaque appel.

    Lus et non figés : la constante précédente était un instantané pris au
    chargement du module, aveugle à toute configuration posée ensuite.

    Raises:
        ImagePresetError: déclaration illisible. Retomber sur les préréglages
            par défaut produirait des variantes que personne n'a demandées,
            aux mauvaises dimensions, sans que rien ne le signale.
    """
    return parse_presets(os.getenv(ENV_VARIANTS, ""))


def preset_names() -> "tuple[str, ...]":
    """Noms des préréglages applicables, dans l'ordre déclaré."""
    return tuple(preset.name for preset in variant_presets())


def preset_by_name(name: str) -> "VariantPreset | None":
    """Préréglage portant ce nom, ou `None` s'il n'est pas déclaré."""
    cible = (name or "").strip().lower()
    for preset in variant_presets():
        if preset.name == cible:
            return preset
    return None
