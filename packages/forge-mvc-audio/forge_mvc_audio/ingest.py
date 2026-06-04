"""Ingestion d'un fichier audio — sans état (aucune base de données).

``ingest_audio`` valide (taille, extension), stocke la source à un emplacement
**uuid-based**, et retourne un enregistrement. Fonction Python appelable depuis
un contrôleur ou un script.

Validation **basique** ici (taille + extension) ; la validation profonde par
``ffprobe`` (vrai flux audio, durée ≤ max) appartient à ``probe_audio``. Aucun
``ffmpeg`` n'est lancé : pas de traitement en ligne.
"""
from __future__ import annotations

import mimetypes
from uuid import uuid4

from forge_mvc_audio.config import AudioConfig, load_audio_config
from forge_mvc_audio.storage import (
    ALLOWED_EXTENSIONS,
    safe_extension,
    store_original,
)

__all__ = ["AudioIngestError", "ingest_audio"]


class AudioIngestError(ValueError):
    """Upload refusé (taille, extension, fichier vide)."""


def ingest_audio(
    data: bytes,
    filename: str,
    *,
    title: str | None = None,
    config: AudioConfig | None = None,
    uuid: str | None = None,
) -> dict:
    """Valide et stocke un fichier audio source.

    Retourne un dict ``{uuid, title, original_path, size_bytes, mime_type}``.
    Lève ``AudioIngestError`` si l'upload est refusé.
    """
    cfg = config or load_audio_config()

    size = len(data)
    if size == 0:
        raise AudioIngestError("fichier vide")
    max_bytes = cfg.max_upload_mb * 1024 * 1024
    if size > max_bytes:
        raise AudioIngestError(
            f"audio trop volumineux : {size} octets > {max_bytes} "
            f"(FORGE_AUDIO_MAX_UPLOAD_MB={cfg.max_upload_mb})"
        )

    ext = safe_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise AudioIngestError(
            f"extension non autorisée : {ext!r} "
            f"(acceptées : {', '.join(sorted(ALLOWED_EXTENSIONS))})"
        )

    audio_uuid = uuid or str(uuid4())
    original_path = store_original(data, audio_uuid, ext, storage_root=cfg.storage_root)
    mime_type = mimetypes.guess_type(filename)[0]

    clean_title = title.strip() if title and title.strip() else None
    return {
        "uuid": audio_uuid,
        "title": clean_title,
        "original_path": original_path,
        "size_bytes": size,
        "mime_type": mime_type,
    }
