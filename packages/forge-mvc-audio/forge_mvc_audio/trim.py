# pyright: strict
"""Découpe d'un fichier audio par début et fin (`AUDIO-TRIM-001`).

Extraire un extrait, retirer un silence de tête, produire un aperçu de trente
secondes : le paquet savait transcoder un fichier entier, pas en prendre un
morceau. Il fallait appeler `ffmpeg` à la main, donc réécrire le durcissement
des arguments et la gestion du délai.

## Ce que le module refuse, et pourquoi

**Il n'écrase jamais la source.** Une découpe sur place n'existe pas côté
`ffmpeg`, qui lit et écrit en même temps : le fichier serait tronqué à zéro et
le travail perdu. Sortie et entrée identiques sont donc refusées.

**Il n'écrase pas un fichier existant sans qu'on le dise.** C'est le mode
« Forge génère » de la charte, write-if-new : un extrait produit deux fois avec
des bornes différentes doit dire lequel gagne.

## Le format de temps

`90`, `1:30` et `0:01:30.5` désignent le même instant. Les trois sont acceptés
parce que les trois se rencontrent, dans une saisie humaine comme dans une
sortie d'outil, et parce que refuser l'un des trois n'apporterait rien.

Ce qui est refusé, en revanche, est un intervalle vide ou renversé : une fin
avant le début produirait un fichier de zéro seconde, que `ffmpeg` écrit sans
se plaindre.
"""
from __future__ import annotations

import re
from pathlib import Path

from forge_mvc_audio.transcode import (
    DEFAULT_TRANSCODE_TIMEOUT,
    FfmpegError,
    FfmpegRunner,
    default_ffmpeg_runner,
    safe_path_arg,
)

__all__ = [
    "AudioTrimError",
    "parse_timecode",
    "format_timecode",
    "build_trim_command",
    "trim_audio",
]

_TIMECODE_RE = re.compile(
    r"^(?:(?:(?P<h>\d+):)?(?P<m>\d{1,2}):)?(?P<s>\d{1,2}(?:\.\d+)?)$"
)


class AudioTrimError(ValueError):
    """Découpe refusée : bornes, chemins, ou intervalle invalides."""


def parse_timecode(value: str) -> float:
    """Instant en secondes. Accepte `SS`, `MM:SS` et `HH:MM:SS`, décimales comprises.

    Raises:
        AudioTrimError: format non reconnu, ou valeur négative.
    """
    texte = (value or "").strip()
    if not texte:
        raise AudioTrimError("instant vide")
    if texte.startswith("-"):
        raise AudioTrimError(f"instant négatif : {texte!r}")

    trouve = _TIMECODE_RE.fullmatch(texte)
    if trouve is None:
        raise AudioTrimError(
            f"instant illisible : {texte!r}. Attendu « SS », « MM:SS » "
            "ou « HH:MM:SS », décimales acceptées."
        )

    heures = int(trouve.group("h") or 0)
    minutes = int(trouve.group("m") or 0)
    secondes = float(trouve.group("s"))
    if trouve.group("m") is not None and secondes >= 60:
        raise AudioTrimError(
            f"secondes hors bornes dans {texte!r} : au delà de 59, écrire des minutes."
        )
    if trouve.group("h") is not None and minutes >= 60:
        raise AudioTrimError(
            f"minutes hors bornes dans {texte!r} : au delà de 59, écrire des heures."
        )
    return heures * 3600 + minutes * 60 + secondes


def format_timecode(seconds: float) -> str:
    """Instant rendu en `HH:MM:SS.mmm`, la forme que `ffmpeg` lit sans ambiguïté."""
    if seconds < 0:
        raise AudioTrimError(f"instant négatif : {seconds}")
    heures, reste = divmod(seconds, 3600)
    minutes, secondes = divmod(reste, 60)
    return f"{int(heures):02d}:{int(minutes):02d}:{secondes:06.3f}"


def build_trim_command(
    ffmpeg_bin: str,
    input_path: str,
    output_path: str,
    *,
    start: float = 0.0,
    end: "float | None" = None,
    reencode: bool = False,
) -> list[str]:
    """Commande de découpe.

    `-ss` est placé **avant** `-i` : `ffmpeg` saute alors directement à
    l'instant demandé au lieu de décoder tout ce qui précède, ce qui change une
    découpe de plusieurs minutes en une opération immédiate sur un long fichier.

    Sans `reencode`, les flux sont copiés tels quels. La découpe est alors
    instantanée et sans perte, mais elle se cale sur l'image clé la plus proche,
    ce qui décale la borne de quelques dixièmes de seconde. `reencode` rend la
    borne exacte, au prix d'un transcodage complet.
    """
    commande = [ffmpeg_bin, "-y", "-ss", format_timecode(start)]
    if end is not None:
        commande += ["-to", format_timecode(end)]
    commande += ["-i", safe_path_arg(input_path), "-vn"]
    commande += (
        ["-c:a", "libmp3lame", "-b:a", "192k"] if reencode else ["-c", "copy"]
    )
    commande.append(safe_path_arg(output_path))
    return commande


def trim_audio(
    input_path: str,
    output_path: str,
    *,
    start: float = 0.0,
    end: "float | None" = None,
    ffmpeg_bin: str = "ffmpeg",
    reencode: bool = False,
    overwrite: bool = False,
    runner: "FfmpegRunner | None" = None,
    timeout: int = DEFAULT_TRANSCODE_TIMEOUT,
) -> None:
    """Découpe `input_path` entre `start` et `end` vers `output_path`.

    Raises:
        AudioTrimError: source absente, sortie identique à la source, sortie
            déjà présente sans `overwrite`, ou intervalle vide ou renversé.
        FfmpegError: `ffmpeg` absent, en échec, ou hors délai.
    """
    source = Path(input_path)
    cible = Path(output_path)

    if not source.is_file():
        raise AudioTrimError(f"source introuvable : {input_path}")

    # Comparaison sur le chemin résolu : `a.mp3` et `./a.mp3` désignent le même
    # fichier, et une comparaison de chaînes les croirait différents.
    if source.resolve() == cible.resolve():
        raise AudioTrimError(
            "la sortie ne peut pas être la source : ffmpeg lit et écrit en "
            "même temps, et le fichier serait tronqué."
        )
    if cible.exists() and not overwrite:
        raise AudioTrimError(
            f"le fichier de sortie existe déjà : {output_path}. "
            "Passer overwrite pour l'écraser."
        )

    if start < 0:
        raise AudioTrimError(f"début négatif : {start}")
    if end is not None and end <= start:
        raise AudioTrimError(
            f"intervalle vide ou renversé : début {start}, fin {end}. "
            "ffmpeg écrirait un fichier de zéro seconde sans se plaindre."
        )

    cible.parent.mkdir(parents=True, exist_ok=True)
    commande = build_trim_command(
        ffmpeg_bin, input_path, output_path, start=start, end=end, reencode=reencode
    )
    code, stderr = (runner or default_ffmpeg_runner)(commande, timeout)
    if code != 0:
        raise FfmpegError(f"ffmpeg a échoué (code {code}) : {stderr.strip()}")
