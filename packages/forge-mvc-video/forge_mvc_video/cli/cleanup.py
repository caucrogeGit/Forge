# pyright: strict
"""Commande ``forge video:cleanup`` — VIDEO-CLEANUP-001.

Purge sûre de l'opt-in vidéo. **dry-run par défaut** : liste ce qui SERAIT
supprimé sans rien toucher ; ``--apply`` exécute réellement.

Usage :
    forge video:cleanup --failed [--apply]
    forge video:cleanup --orphan-files [--apply]
    forge video:cleanup --failed --orphan-files [--apply]

- ``--failed``       : supprime les vidéos en statut ``failed`` (ligne ``videos``
                       + fichiers original / mp4 / poster) ;
- ``--orphan-files`` : supprime les fichiers du stockage non référencés en base ;
- ``--apply``        : exécute réellement (sinon dry-run, rien n'est touché).

Sécurité : aucune suppression hors de ``storage_root`` (anti-traversal sur les
chemins issus de la base).
"""
from __future__ import annotations

import os
from collections.abc import Callable, Iterator

from forge_mvc_video.config import VideoConfig, load_video_config
from forge_mvc_video.storage.repository import STATUS_FAILED, VideoRepository

__all__ = ["run_cleanup", "main"]

STATUS_OK = "[OK]"
STATUS_INFO = "[INFO]"
STATUS_ERROR = "[ERREUR]"
STATUS_DRY = "[DRY-RUN]"


def _safe_abspath(storage_root: str, relpath: str) -> str | None:
    """Joint ``relpath`` sous ``storage_root`` en refusant toute évasion.

    Retourne ``None`` si le chemin résolu sort de ``storage_root`` (``..``,
    chemin absolu, lien) — défense anti-traversal.
    """
    root = os.path.realpath(storage_root)
    candidate = os.path.realpath(os.path.join(root, relpath))
    if candidate == root or candidate.startswith(root + os.sep):
        return candidate
    return None


def _iter_storage_files(storage_root: str) -> Iterator[tuple[str, str]]:
    """Itère ``(relpath_posix, abspath)`` de tous les fichiers sous la racine."""
    root = os.path.realpath(storage_root)
    if not os.path.isdir(root):
        return
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            full = os.path.join(dirpath, name)
            rel = os.path.relpath(full, root).replace(os.sep, "/")
            yield rel, full


def run_cleanup(
    args: list[str],
    *,
    config: VideoConfig | None = None,
    repository: VideoRepository | None = None,
    remove_file: Callable[[str], None] | None = None,
) -> int:
    """Cœur testable de ``video:cleanup``. Briques injectables.

    Retourne : 2 (usage), 0 (succès, dry-run ou apply).
    """
    cfg = config or load_video_config()
    repo = repository or VideoRepository()
    remove = remove_file or os.remove

    apply = "--apply" in args
    do_failed = "--failed" in args
    do_orphans = "--orphan-files" in args

    if not (do_failed or do_orphans):
        print(f"{STATUS_ERROR} cible manquante.")
        print(
            "Usage : forge video:cleanup [--failed] [--orphan-files] [--apply]"
        )
        return 2

    tag = STATUS_OK if apply else STATUS_DRY
    removed_files = 0
    removed_rows = 0

    def _maybe_remove(abspath: str | None, label: str) -> None:
        nonlocal removed_files
        if abspath is None or not os.path.isfile(abspath):
            return
        print(f"{tag} fichier : {label}")
        removed_files += 1
        if apply:
            try:
                remove(abspath)
            except OSError as exc:
                print(f"{STATUS_ERROR} suppression échouée ({label}) : {exc}")

    if do_failed:
        for row in repo.list_by_status(STATUS_FAILED):
            video_id = row["id"]
            for key in ("original_path", "mp4_path", "poster_path"):
                rel = row.get(key)
                if rel:
                    _maybe_remove(_safe_abspath(cfg.storage_root, rel), rel)
            print(f"{tag} ligne DB : vidéo failed id={video_id}")
            removed_rows += 1
            if apply:
                repo.delete(video_id)

    if do_orphans:
        referenced = repo.all_relpaths()
        for rel, full in _iter_storage_files(cfg.storage_root):
            if rel not in referenced:
                _maybe_remove(full, rel)

    suffix = "supprimé(s)" if apply else "à supprimer (dry-run)"
    print(
        f"{STATUS_INFO} {removed_files} fichier(s), {removed_rows} ligne(s) "
        f"{suffix}."
    )
    if not apply and (removed_files or removed_rows):
        print(f"{STATUS_INFO} relance avec --apply pour exécuter réellement.")
    return 0


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` (projet = répertoire courant)."""
    return run_cleanup(args or [])
