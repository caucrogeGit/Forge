# pyright: strict
"""Métadonnées d'un fichier audio, dites ID3 (`AUDIO-ID3-001`).

`ffprobe` rend déjà ces étiquettes, le paquet les jetait : le sondage lisait la
durée, le codec et le débit, et laissait tomber le titre, l'artiste et l'album.
Une application devait donc rappeler `ffprobe` elle même pour afficher le nom
d'un morceau qu'elle venait de recevoir.

## Ce qui rend ce module moins anodin qu'il n'y paraît

**Une étiquette vient du fichier envoyé.** Elle est écrite par qui a produit le
fichier, ou par qui l'a modifié avant de l'envoyer, et elle finit affichée dans
une page.

Trois précautions en découlent, appliquées ici plutôt que laissées à l'appelant,
qui les oublierait une fois sur deux.

- Les caractères de contrôle sont retirés. Un saut de ligne dans un titre casse
  un en-tête HTTP si l'application le remet dans un `Content-Disposition`, et
  `U+2028` casse une chaîne JavaScript.
- La longueur est bornée. Rien n'empêche un titre d'un mégaoctet, qui n'est pas
  un titre.
- Rien n'est interprété. Le module ne décode aucune entité, ne suit aucune URL
  et n'échappe rien : l'échappement appartient au gabarit, et le faire deux fois
  afficherait `&amp;amp;`.

Le module ne réécrit **jamais** les étiquettes d'un fichier. Les lire et les
écrire sont deux gestes, et le second appartiendrait à un autre ticket.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, cast

__all__ = [
    "AudioTags",
    "MAX_TAG_LENGTH",
    "clean_tag_value",
    "parse_tags",
]

#: Au delà, ce n'est plus une étiquette. Large pour un titre d'opéra.
MAX_TAG_LENGTH = 300

#: Un conteneur nomme ses étiquettes à sa façon : ID3 dit `track`, Vorbis dit
#: `TRACKNUMBER`, et la casse varie. Les clés sont donc cherchées en minuscules,
#: par ordre de préférence.
_ALIASES: "dict[str, tuple[str, ...]]" = {
    "title": ("title", "tit2"),
    "artist": ("artist", "tpe1", "author"),
    "album": ("album", "talb"),
    "album_artist": ("album_artist", "albumartist", "tpe2"),
    "genre": ("genre", "tcon"),
    "comment": ("comment", "comm", "description"),
    "date": ("date", "year", "tyer", "tdrc", "originaldate"),
    "track": ("track", "tracknumber", "trck"),
}

_ANNEE_RE = re.compile(r"(\d{4})")
_PISTE_RE = re.compile(r"^\s*(\d{1,4})\s*(?:/\s*(\d{1,4})\s*)?$")

#: Bornes d'une année plausible. Le premier enregistrement sonore date de 1860 ;
#: au delà de 2999 ce n'est plus une date mais une erreur de saisie.
_ANNEE_MIN = 1860
_ANNEE_MAX = 2999


@dataclass(frozen=True)
class AudioTags:
    """Étiquettes lues, nettoyées. Tout est facultatif, et souvent absent."""

    title: "str | None" = None
    artist: "str | None" = None
    album: "str | None" = None
    album_artist: "str | None" = None
    genre: "str | None" = None
    comment: "str | None" = None
    year: "int | None" = None
    track_number: "int | None" = None
    track_total: "int | None" = None

    @property
    def is_empty(self) -> bool:
        """Vrai si le fichier ne porte aucune étiquette exploitable.

        Le cas courant d'un enregistrement brut ou d'un fichier converti avec
        `-map_metadata -1`, ce que fait le transcodage du paquet.
        """
        return all(
            getattr(self, champ.name) is None for champ in self.__dataclass_fields__.values()
        )

    @property
    def display_title(self) -> "str | None":
        """Titre affichable, artiste compris quand il est connu."""
        if self.title and self.artist:
            return f"{self.artist} - {self.title}"
        return self.title or self.artist


def clean_tag_value(value: object) -> "str | None":
    """Étiquette nettoyée, ou `None` si elle ne dit rien.

    Retire les caractères de contrôle et les séparateurs de ligne Unicode, y
    compris `U+2028` et `U+2029` que `str.strip` laisse passer, puis borne la
    longueur. N'échappe rien : l'échappement appartient au gabarit.
    """
    if value is None:
        return None
    texte = str(value)
    # Catégories Unicode Cc (contrôle), Cf (format), Zl et Zp (séparateurs de
    # ligne et de paragraphe). L'espace ordinaire et les lettres restent.
    nettoye = "".join(
        " " if unicodedata.category(c) in {"Cc", "Zl", "Zp"} else c
        for c in texte
        if unicodedata.category(c) != "Cf"
    )
    nettoye = " ".join(nettoye.split())
    if not nettoye:
        return None
    if len(nettoye) > MAX_TAG_LENGTH:
        nettoye = nettoye[:MAX_TAG_LENGTH].rstrip()
    return nettoye or None


def _premier(tags: "dict[str, Any]", champ: str) -> "str | None":
    for alias in _ALIASES[champ]:
        if alias in tags:
            valeur = clean_tag_value(tags[alias])
            if valeur is not None:
                return valeur
    return None


def _annee(brut: "str | None") -> "int | None":
    """Année extraite d'une date. `2019-05-01T00:00:00Z` donne 2019.

    Une valeur hors des bornes plausibles est écartée : afficher « année 20 »
    ou « année 90210 » vaut moins que ne rien afficher.
    """
    if not brut:
        return None
    trouve = _ANNEE_RE.search(brut)
    if trouve is None:
        return None
    annee = int(trouve.group(1))
    return annee if _ANNEE_MIN <= annee <= _ANNEE_MAX else None


def _piste(brut: "str | None") -> "tuple[int | None, int | None]":
    """Numéro et total de piste. `3/12` donne `(3, 12)`, `3` donne `(3, None)`."""
    if not brut:
        return (None, None)
    trouve = _PISTE_RE.fullmatch(brut)
    if trouve is None:
        return (None, None)
    numero = int(trouve.group(1))
    total = int(trouve.group(2)) if trouve.group(2) else None
    if numero == 0:
        return (None, None)
    if total is not None and (total == 0 or total < numero):
        # Un total inférieur au numéro est une saisie fausse ; garder le numéro
        # seul vaut mieux que d'afficher « piste 5 sur 2 ».
        total = None
    return (numero, total)


def _absorber(cible: "dict[str, Any]", etiquettes: object) -> None:
    """Verse un bloc d'étiquettes dans `cible`, clés en minuscules.

    La sortie de `ffprobe` est du JSON décodé, donc non typée : le contenu est
    ramené à un dictionnaire de chaînes avant d'être lu.
    """
    if not isinstance(etiquettes, dict):
        return
    for cle, valeur in cast("dict[Any, Any]", etiquettes).items():
        cible[str(cle).strip().lower()] = valeur


def parse_tags(payload: "dict[str, Any] | None") -> AudioTags:
    """Étiquettes d'une sortie `ffprobe` décodée.

    Les étiquettes vivent dans `format.tags`, et parfois seulement dans celles
    du flux audio : un conteneur comme le WAV ne porte pas de bloc de format,
    et les deux sources sont donc réunies, le format l'emportant.

    Ne lève jamais. Un fichier sans étiquette est le cas courant, pas une
    erreur, et une exception ici ferait échouer un envoi parfaitement valide.
    """
    if not isinstance(payload, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        return AudioTags()

    reunies: "dict[str, Any]" = {}
    flux = payload.get("streams")
    if isinstance(flux, list):
        for brut in cast("list[Any]", flux):
            element = cast("dict[str, Any]", brut) if isinstance(brut, dict) else None
            if element is None or element.get("codec_type") != "audio":
                continue
            _absorber(reunies, element.get("tags"))
            break

    format_ = payload.get("format")
    if isinstance(format_, dict):
        _absorber(reunies, cast("dict[str, Any]", format_).get("tags"))

    numero, total = _piste(_premier(reunies, "track"))
    return AudioTags(
        title=_premier(reunies, "title"),
        artist=_premier(reunies, "artist"),
        album=_premier(reunies, "album"),
        album_artist=_premier(reunies, "album_artist"),
        genre=_premier(reunies, "genre"),
        comment=_premier(reunies, "comment"),
        year=_annee(_premier(reunies, "date")),
        track_number=numero,
        track_total=total,
    )
