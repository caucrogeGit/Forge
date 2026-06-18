# pyright: strict
"""Commande ``forge video:upload`` — VIDEO-UPLOAD-CLI-001.

Entrée d'upload **officielle** d'une vidéo source : lit le fichier, le valide
(taille, extension), le stocke à un emplacement uuid-based et insère une ligne
``videos`` au statut ``uploaded``. C'est le pendant CLI de ``ingest_video`` ;
le traitement lourd (probe + poster + transcodage MP4) reste à
``forge video:process``.

Usage :
    forge video:upload <fichier> [--title "Titre"]

N'exécute aucun ffmpeg (pas de traitement en ligne) : relancer
``forge video:process <id>`` ensuite pour générer le MP4 et le poster.
"""
from __future__ import annotations

import os
from collections.abc import Callable
from typing import Any

from forge_mvc_video.config import VideoConfig
from forge_mvc_video.ingest import VideoIngestError, ingest_video
from forge_mvc_video.storage.repository import VideoRepository

__all__ = ["run_upload", "main"]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"


def _default_read(path: str) -> bytes:
    with open(path, "rb") as handle:
        return handle.read()


def _parse_title(args: list[str]) -> tuple[str | None, list[str]]:
    """Extrait ``--title <valeur>`` ou ``--title=<valeur>``.

    Retourne ``(title, positionnels)``.
    """
    title: str | None = None
    rest: list[str] = []
    index = 0
    while index < len(args):
        arg = args[index]
        if arg == "--title":
            if index + 1 < len(args):
                title = args[index + 1]
                index += 2
                continue
            index += 1
            continue
        if arg.startswith("--title="):
            title = arg[len("--title="):]
            index += 1
            continue
        rest.append(arg)
        index += 1
    return title, rest


def run_upload(
    args: list[str],
    *,
    config: VideoConfig | None = None,
    repository: VideoRepository | None = None,
    ingest_fn: Callable[..., dict[str, Any]] | None = None,
    read_file: Callable[[str], bytes] | None = None,
) -> int:
    """Cœur testable de ``video:upload``. Briques injectables.

    Retourne : 2 (usage / fichier introuvable), 1 (upload refusé), 0 (succès).
    """
    ingest = ingest_fn or ingest_video
    reader = read_file or _default_read

    title, positionals = _parse_title(list(args))

    if not positionals:
        print(f"{STATUS_ERROR} fichier manquant.")
        print('Usage : forge video:upload <fichier> [--title "Titre"]')
        return 2

    path = positionals[0]
    if not os.path.isfile(path):
        print(f"{STATUS_ERROR} fichier introuvable : {path}")
        return 2

    try:
        data = reader(path)
    except OSError as exc:
        print(f"{STATUS_ERROR} lecture impossible : {exc}")
        return 2

    filename = os.path.basename(path)
    try:
        result = ingest(
            data, filename, title=title, config=config, repository=repository
        )
    except VideoIngestError as exc:
        print(f"{STATUS_ERROR} upload refusé : {exc}")
        return 1

    print(
        f"{STATUS_OK} vidéo uploadée → id={result['id']} uuid={result['uuid']}"
    )
    print(
        f"{STATUS_INFO} statut : {result['status']} — lance "
        f"`forge video:process {result['id']}` pour générer le MP4 et le poster."
    )
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` (projet = répertoire courant)."""
    return run_upload(args or [])
