"""Commande ``forge video:process`` — VIDEO-CLI-001.

Déclenche le traitement (probe + poster + transcodage MP4) d'une vidéo, ou de
toutes les vidéos en attente. C'est le **worker CLI** : le travail lourd se fait
ici, jamais pendant une requête HTTP.

Usage :
    forge video:process <id>        # traite une vidéo
    forge video:process --pending   # traite toutes les vidéos `uploaded`

ffmpeg/ffprobe sont requis pour le transcodage (vérifier avec
``forge video:doctor``). Une vidéo dont le traitement échoue passe en
``failed`` (avec un message) sans interrompre les autres.
"""
from __future__ import annotations

from forge_mvc_video.process import VideoProcessError, process_video
from forge_mvc_video.storage.repository import (
    STATUS_UPLOADED,
    VideoRepository,
)

__all__ = ["run_process", "main"]

STATUS_OK = "[OK]"
STATUS_FAIL = "[FAIL]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"


def run_process(
    args: list[str],
    *,
    repository: VideoRepository | None = None,
    config=None,
    process_fn=None,
) -> int:
    """Cœur testable de ``video:process``. Briques injectables.

    Retourne : 2 (usage), 1 (au moins un échec / erreur), 0 (succès).
    """
    repo = repository or VideoRepository()
    proc = process_fn or process_video

    pending = "--pending" in args
    positionals = [a for a in args if not a.startswith("-")]

    if pending:
        ids = [row["id"] for row in repo.list_by_status(STATUS_UPLOADED)]
    elif positionals:
        try:
            ids = [int(positionals[0])]
        except ValueError:
            print(f"{STATUS_ERROR} id invalide : {positionals[0]!r}")
            return 2
    else:
        print(f"{STATUS_ERROR} id manquant.")
        print("Usage : forge video:process <id> | --pending")
        return 2

    if not ids:
        print(f"{STATUS_INFO} aucune vidéo à traiter.")
        return 0

    failures = 0
    for video_id in ids:
        try:
            result = proc(video_id, config=config, repository=repo)
        except VideoProcessError as exc:
            print(f"{STATUS_ERROR} vidéo {video_id} : {exc}")
            failures += 1
            continue
        if result.get("status") == "ready":
            print(f"{STATUS_OK} vidéo {video_id} → ready ({result.get('mp4_path')})")
        else:
            print(f"{STATUS_FAIL} vidéo {video_id} → failed : {result.get('error')}")
            failures += 1

    return 1 if failures else 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` (config + projet = répertoire courant)."""
    return run_process(args or [])
