"""Ingestion d'une vidéo source — VIDEO-UPLOAD-STORE-001.

``ingest_video`` : valide (taille, extension), stocke la source à un
emplacement **uuid-based**, et insère une ligne ``videos`` au statut
``uploaded``. Fonction Python appelable depuis un contrôleur ou un script —
le branchement HTTP (route d'upload) viendra dans un ticket ultérieur.

Validation **basique** ici (taille + extension) : la validation profonde par
``ffprobe`` (vrai conteneur, durée ≤ max) appartient à ``VIDEO-PROBE-METADATA``.
Aucun ``ffmpeg`` n'est lancé : pas de traitement en ligne (modèle worker CLI).
"""
from __future__ import annotations

import mimetypes
from datetime import UTC, datetime
from uuid import uuid4

from forge_mvc_video.config import VideoConfig, load_video_config
from forge_mvc_video.storage.files import (
    ALLOWED_EXTENSIONS,
    safe_extension,
    store_original,
)
from forge_mvc_video.storage.repository import VideoRepository

__all__ = ["VideoIngestError", "ingest_video"]


class VideoIngestError(ValueError):
    """Upload refusé (taille, extension, fichier vide)."""


def ingest_video(
    data: bytes,
    filename: str,
    *,
    title: str | None = None,
    config: VideoConfig | None = None,
    repository: VideoRepository | None = None,
    now: datetime | None = None,
) -> dict:
    """Valide, stocke et enregistre une vidéo source.

    Retourne un dict ``{id, uuid, title, original_path, size_bytes, status}``.
    Lève ``VideoIngestError`` si l'upload est refusé.
    """
    cfg = config or load_video_config()
    repo = repository or VideoRepository()
    moment = now or datetime.now(UTC).replace(tzinfo=None)

    size = len(data)
    if size == 0:
        raise VideoIngestError("fichier vide")
    max_bytes = cfg.max_upload_mb * 1024 * 1024
    if size > max_bytes:
        raise VideoIngestError(
            f"vidéo trop volumineuse : {size} octets > {max_bytes} "
            f"(FORGE_VIDEO_MAX_UPLOAD_MB={cfg.max_upload_mb})"
        )

    ext = safe_extension(filename)
    if ext not in ALLOWED_EXTENSIONS:
        raise VideoIngestError(
            f"extension non autorisée : {ext!r} "
            f"(acceptées : {', '.join(sorted(ALLOWED_EXTENSIONS))})"
        )

    video_uuid = str(uuid4())
    original_path = store_original(
        data, video_uuid, ext, storage_root=cfg.storage_root, now=moment
    )
    mime_type = mimetypes.guess_type(filename)[0]

    clean_title = title.strip() if title and title.strip() else None
    video_id = repo.insert_uploaded(
        uuid=video_uuid,
        title=clean_title,
        original_path=original_path,
        size_bytes=size,
        mime_type=mime_type,
        now=moment,
    )
    return {
        "id": video_id,
        "uuid": video_uuid,
        "title": clean_title,
        "original_path": original_path,
        "size_bytes": size,
        "status": "uploaded",
    }
