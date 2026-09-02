# pyright: strict
"""Commande ``forge audio:trim`` (`AUDIO-TRIM-001`).

Découpe un fichier audio entre deux instants, sans toucher à la source.

La commande n'ouvre aucune connexion et ne lit aucune base : le paquet audio
est sans état, et cette commande ne change rien à cela.
"""
from __future__ import annotations

from pathlib import Path

from forge_mvc_audio.config import load_audio_config
from forge_mvc_audio.transcode import FfmpegError
from forge_mvc_audio.trim import AudioTrimError, parse_timecode, trim_audio

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"

__all__ = ["STATUS_OK", "STATUS_INFO", "STATUS_ERROR", "parse_options", "main"]


class _Options:
    def __init__(self) -> None:
        self.source: "str | None" = None
        self.sortie: "str | None" = None
        self.debut = "0"
        self.fin: "str | None" = None
        self.reencode = False
        self.force = False
        self.error: "str | None" = None


def _valeur(argv: list[str], index: int, argument: str) -> "tuple[str | None, int]":
    if "=" in argument:
        return argument.partition("=")[2], index
    if index + 1 >= len(argv):
        return None, index
    return argv[index + 1], index + 1


def parse_options(argv: list[str]) -> _Options:
    """Lit les arguments. Un argument inconnu est une erreur, jamais un silence."""
    options = _Options()
    positionnels: list[str] = []
    index = 0
    while index < len(argv):
        argument = argv[index]
        nom = argument.partition("=")[0]
        if nom in {"--from", "--start"}:
            valeur, index = _valeur(argv, index, argument)
            if valeur is None:
                options.error = f"L'option {nom} attend un instant."
                return options
            options.debut = valeur
        elif nom in {"--to", "--end"}:
            valeur, index = _valeur(argv, index, argument)
            if valeur is None:
                options.error = f"L'option {nom} attend un instant."
                return options
            options.fin = valeur
        elif argument == "--reencode":
            options.reencode = True
        elif argument == "--force":
            options.force = True
        elif argument.startswith("-"):
            options.error = f"Option inconnue : {argument!r}."
            return options
        else:
            positionnels.append(argument)
        index += 1

    if len(positionnels) != 2:
        options.error = (
            "Usage : forge audio:trim SOURCE SORTIE [--from INSTANT] [--to INSTANT]"
        )
        return options
    options.source, options.sortie = positionnels

    try:
        debut = parse_timecode(options.debut)
        fin = parse_timecode(options.fin) if options.fin is not None else None
    except AudioTrimError as exc:
        options.error = str(exc)
        return options
    if fin is not None and fin <= debut:
        options.error = (
            f"Intervalle vide ou renversé : début {options.debut}, fin {options.fin}."
        )
    return options


def main(args: "list[str] | None" = None) -> int:
    options = parse_options(list(args or []))
    if options.error:
        print(f"{STATUS_ERROR} {options.error}")
        return 1

    assert options.source is not None and options.sortie is not None
    debut = parse_timecode(options.debut)
    fin = parse_timecode(options.fin) if options.fin is not None else None

    try:
        config = load_audio_config()
    except ValueError as exc:
        print(f"{STATUS_ERROR} {exc}")
        return 1

    borne = f"de {options.debut}" + (f" à {options.fin}" if options.fin else " à la fin")
    print(f"{STATUS_INFO} Découpe {borne}, sans toucher à {options.source}.")

    try:
        trim_audio(
            options.source,
            options.sortie,
            start=debut,
            end=fin,
            ffmpeg_bin=config.ffmpeg_bin,
            reencode=options.reencode,
            overwrite=options.force,
        )
    except AudioTrimError as exc:
        print(f"{STATUS_ERROR} {exc}")
        return 1
    except FfmpegError as exc:
        print(f"{STATUS_ERROR} {exc}")
        return 1

    taille = Path(options.sortie).stat().st_size
    print(f"{STATUS_OK} Écrit : {options.sortie} ({taille} octets)")
    if not options.reencode:
        print(
            f"{STATUS_INFO} Flux copié sans réencodage : les bornes se calent "
            "sur l'image clé la plus proche. --reencode les rend exactes."
        )
    return 0
