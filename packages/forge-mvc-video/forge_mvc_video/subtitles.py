# pyright: strict
"""Pistes de sous-titres associées à une vidéo (`VIDEO-SUBTITLES-001`).

Une vidéo sans sous-titres est inaccessible aux personnes sourdes ou
malentendantes, illisible dans un environnement bruyant, et introuvable par une
recherche textuelle. Le paquet savait transcoder et servir, pas accompagner.

## Un seul format, WebVTT

C'est le seul que la balise `<track>` de HTML lit nativement, sans script ni
conversion. En accepter d'autres, SRT ou ASS, demanderait de convertir à la
volée ou de faire porter la conversion au navigateur, qui ne sait pas la faire :
le principe 11 veut une seule façon officielle.

## Ce que la validation refuse, et pourquoi

Le fichier est servi au navigateur et lu comme du texte. Un fichier qui n'est
pas du WebVTT est donc refusé **à l'entrée**, sur sa signature.

Sans ce contrôle, n'importe quel fichier pourrait être stocké et servi depuis
le domaine de l'application sous un nom rassurant. Le refuser à l'écriture vaut
mieux que de le filtrer à chaque lecture : la ligne ne doit pas exister.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

__all__ = [
    "SubtitleError",
    "SubtitleTrack",
    "VTT_MIME_TYPE",
    "MAX_SUBTITLE_BYTES",
    "normalize_lang",
    "validate_vtt",
    "subtitle_relpath",
    "store_subtitle",
]

#: Type servi au navigateur. `text/vtt` est exigé par la balise `<track>`.
VTT_MIME_TYPE = "text/vtt; charset=utf-8"

#: Un fichier de sous-titres d'un long métrage pèse quelques dizaines de
#: kilooctets. Un mégaoctet laisse une marge large sans ouvrir la porte à un
#: envoi qui n'en serait pas un.
MAX_SUBTITLE_BYTES = 1024 * 1024

#: Étiquette de langue BCP 47 simplifiée : « fr », « en-GB », « zh-Hans ».
_LANG_RE = re.compile(r"^[A-Za-z]{2,8}(-[A-Za-z0-9]{2,8})*$")

#: Signature obligatoire d'un fichier WebVTT, éventuellement précédée du BOM.
_BOM = "﻿"


class SubtitleError(ValueError):
    """Piste de sous-titres refusée."""


@dataclass(frozen=True)
class SubtitleTrack:
    """Une piste, telle qu'un gabarit la rend en balise `<track>`."""

    lang: str
    path: str
    label: "str | None" = None
    is_default: bool = False

    @property
    def display_label(self) -> str:
        """Ce que le lecteur affiche. La langue à défaut d'étiquette."""
        return self.label or self.lang


def normalize_lang(lang: str) -> str:
    """Étiquette de langue normalisée, ou lève.

    La casse est ramenée en minuscules pour que `FR` et `fr` ne créent pas deux
    pistes que la contrainte d'unicité laisserait passer et que le lecteur
    afficherait deux fois.

    Raises:
        SubtitleError: étiquette vide ou hors du format BCP 47.
    """
    valeur = (lang or "").strip()
    if not valeur:
        raise SubtitleError("la langue d'une piste ne peut pas être vide")
    if not _LANG_RE.fullmatch(valeur):
        raise SubtitleError(
            f"étiquette de langue invalide : {valeur!r}. "
            "Attendu une étiquette BCP 47, « fr », « en-GB » ou « zh-Hans »."
        )
    return valeur.lower()


def validate_vtt(data: bytes) -> str:
    """Vérifie que `data` est bien du WebVTT, et le rend décodé.

    Le contrôle porte sur la signature `WEBVTT`, que la spécification exige en
    tête de fichier. C'est ce qui distingue un sous-titre d'un fichier quelconque
    déposé sous une extension `.vtt`.

    Raises:
        SubtitleError: fichier vide, trop lourd, non décodable en UTF-8, ou
            dépourvu de la signature.
    """
    if not data:
        raise SubtitleError("fichier de sous-titres vide")
    if len(data) > MAX_SUBTITLE_BYTES:
        raise SubtitleError(
            f"fichier de sous-titres trop lourd : {len(data)} octets > "
            f"{MAX_SUBTITLE_BYTES}"
        )
    try:
        texte = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise SubtitleError(
            "fichier de sous-titres illisible : le WebVTT est en UTF-8"
        ) from exc

    sans_bom = texte[1:] if texte.startswith(_BOM) else texte
    premiere = sans_bom.split("\n", 1)[0].strip()
    # La spécification autorise « WEBVTT », « WEBVTT - titre » et
    # « WEBVTT<tabulation>titre ». Elle n'autorise rien d'autre.
    if premiere != "WEBVTT" and not premiere.startswith(("WEBVTT ", "WEBVTT\t", "WEBVTT-")):
        raise SubtitleError(
            "le fichier ne commence pas par la signature WEBVTT : ce n'est pas "
            "un fichier WebVTT. Convertissez votre SRT avant de l'envoyer."
        )
    return sans_bom


def subtitle_relpath(video_uuid: str, lang: str) -> str:
    """Chemin relatif d'une piste sous la racine de stockage.

    Bâti depuis l'UUID de la vidéo et l'étiquette de langue, tous deux déjà
    validés : le nom de fichier envoyé par l'utilisateur n'entre pas dans le
    chemin, et aucune traversée n'est donc possible.
    """
    return f"subtitles/{video_uuid}/{normalize_lang(lang)}.vtt"


def store_subtitle(
    data: bytes, video_uuid: str, lang: str, *, storage_root: "str | Path"
) -> str:
    """Valide puis écrit une piste. Rend son chemin relatif.

    Raises:
        SubtitleError: le contenu n'est pas du WebVTT valide.
    """
    texte = validate_vtt(data)
    relatif = subtitle_relpath(video_uuid, lang)

    racine = Path(storage_root).resolve()
    cible = (racine / relatif).resolve()
    if not cible.is_relative_to(racine):
        raise SubtitleError("chemin de sous-titres hors du dossier de stockage")

    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(texte, encoding="utf-8")
    return relatif
