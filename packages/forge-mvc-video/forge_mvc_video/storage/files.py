"""Disposition des fichiers vidéo sur disque — VIDEO-UPLOAD-STORE-001.

Le stockage est **uuid-based** : le nom de fichier fourni par l'utilisateur
n'apparaît **jamais** dans le chemin (anti-traversal par construction). Seule
l'extension, validée contre une liste blanche, est conservée.

Disposition (sous ``FORGE_VIDEO_STORAGE_ROOT``) :

    originals/<AAAA>/<MM>/<uuid>/source<ext>
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

__all__ = [
    "ALLOWED_EXTENSIONS",
    "safe_extension",
    "original_relpath",
    "mp4_relpath",
    "poster_relpath",
    "store_original",
]

# Conteneurs acceptés en entrée (la sortie garantie reste MP4, plus tard).
ALLOWED_EXTENSIONS = frozenset({".mp4", ".mov", ".webm", ".mkv"})


def safe_extension(filename: str) -> str:
    """Extension en minuscules du nom fourni (``""`` si aucune)."""
    return Path(filename or "").suffix.lower()


def _partition(now: datetime | None) -> datetime:
    return now or datetime.now(UTC).replace(tzinfo=None)


def original_relpath(uuid: str, ext: str, *, now: datetime | None = None) -> str:
    """Chemin relatif de la source, partitionné par date, uuid-based."""
    return f"originals/{_partition(now):%Y/%m}/{uuid}/source{ext}"


def mp4_relpath(uuid: str, *, now: datetime | None = None) -> str:
    """Chemin relatif du MP4 transcodé (uuid-based)."""
    return f"mp4/{_partition(now):%Y/%m}/{uuid}/video.mp4"


def poster_relpath(uuid: str, *, now: datetime | None = None) -> str:
    """Chemin relatif du poster JPG (uuid-based)."""
    return f"posters/{_partition(now):%Y/%m}/{uuid}/poster.jpg"


def store_original(
    data: bytes,
    uuid: str,
    ext: str,
    *,
    storage_root: str,
    now: datetime | None = None,
) -> str:
    """Écrit la source à un emplacement uuid-based ; retourne le chemin relatif."""
    rel = original_relpath(uuid, ext, now=now)
    target = Path(storage_root) / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    return rel
