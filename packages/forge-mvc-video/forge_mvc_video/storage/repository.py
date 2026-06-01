"""Repository de la table ``videos`` — VIDEO-UPLOAD-STORE-001.

Persistance du cycle de vie d'une vidéo (uploaded → processing →
ready/failed). Le SQL reste **visible** ici ; l'exécution est déléguée à un
*adapter* injectable (par défaut ``core.database.db``), ce qui rend le
repository testable **sans base réelle** (mêmes principes que le repository
IoT Forge).

Ce ticket reste scoped persistance : ni HTTP, ni transcodage, ni ffprobe.
Le repository ne **crée pas** la table — la migration ``videos`` doit avoir
été appliquée (``forge video:init`` puis ``forge migration:apply``).

Sens des dépendances respecté : ``forge-mvc-video`` dépend de ``forge-mvc``
(``core.database``), jamais l'inverse.
"""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Protocol

__all__ = [
    "TABLE",
    "STATUS_UPLOADED",
    "STATUS_PROCESSING",
    "STATUS_READY",
    "STATUS_FAILED",
    "VALID_STATUSES",
    "DbAdapter",
    "VideoRepository",
]

TABLE = "videos"

STATUS_UPLOADED = "uploaded"
STATUS_PROCESSING = "processing"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
VALID_STATUSES = frozenset({
    STATUS_UPLOADED, STATUS_PROCESSING, STATUS_READY, STATUS_FAILED,
})

_INSERT_SQL = (
    "INSERT INTO videos "
    "(uuid, title, original_path, size_bytes, mime_type, status, "
    "created_at, updated_at) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
)
_SELECT_BY_UUID_SQL = "SELECT * FROM videos WHERE uuid = %s"
_SELECT_BY_ID_SQL = "SELECT * FROM videos WHERE id = %s"
_UPDATE_STATUS_SQL = (
    "UPDATE videos SET status = %s, error_message = %s, updated_at = %s "
    "WHERE id = %s"
)
_UPDATE_METADATA_SQL = (
    "UPDATE videos SET duration_seconds = %s, width = %s, height = %s, "
    "updated_at = %s WHERE id = %s"
)
_MARK_READY_SQL = (
    "UPDATE videos SET status = %s, mp4_path = %s, poster_path = %s, "
    "error_message = NULL, updated_at = %s WHERE id = %s"
)
_SELECT_RECENT_SQL = "SELECT * FROM videos ORDER BY id DESC LIMIT %s"
_SELECT_BY_STATUS_SQL = (
    "SELECT * FROM videos WHERE status = %s ORDER BY id ASC LIMIT %s"
)


class DbAdapter(Protocol):
    """Interface attendue, conforme à ``core.database.db``."""

    def insert(self, sql: str, params: tuple) -> int:  # pragma: no cover - protocole
        ...

    def execute(self, sql: str, params: tuple) -> Any:  # pragma: no cover - protocole
        ...

    def fetch_one(self, sql: str, params: tuple) -> dict | None:  # pragma: no cover - protocole
        ...

    def fetch_all(self, sql: str, params: tuple) -> list[dict]:  # pragma: no cover - protocole
        ...


def _default_db_adapter() -> Any:
    """Importe paresseusement ``core.database.db`` (aucune connexion à l'import)."""
    from core.database import db

    return db


def _utcnow() -> datetime:
    """Horodatage UTC naïf, compatible colonne ``DATETIME(6)``."""
    return datetime.now(UTC).replace(tzinfo=None)


class VideoRepository:
    """CRUD minimal de la table ``videos``."""

    def __init__(self, db_adapter: DbAdapter | None = None) -> None:
        self._db = db_adapter or _default_db_adapter()

    def insert_uploaded(
        self,
        *,
        uuid: str,
        original_path: str,
        size_bytes: int,
        mime_type: str | None = None,
        title: str | None = None,
        now: datetime | None = None,
    ) -> int:
        """Insère une vidéo au statut ``uploaded`` ; retourne son ``id``."""
        ts = now or _utcnow()
        return self._db.insert(
            _INSERT_SQL,
            (uuid, title, original_path, size_bytes, mime_type, STATUS_UPLOADED, ts, ts),
        )

    def get_by_uuid(self, uuid: str) -> dict | None:
        return self._db.fetch_one(_SELECT_BY_UUID_SQL, (uuid,))

    def get_by_id(self, video_id: int) -> dict | None:
        return self._db.fetch_one(_SELECT_BY_ID_SQL, (video_id,))

    def update_status(
        self,
        video_id: int,
        status: str,
        *,
        error_message: str | None = None,
        now: datetime | None = None,
    ) -> None:
        if status not in VALID_STATUSES:
            raise ValueError(
                f"statut invalide : {status!r} (attendu {sorted(VALID_STATUSES)})"
            )
        self._db.execute(
            _UPDATE_STATUS_SQL, (status, error_message, now or _utcnow(), video_id)
        )

    def update_metadata(
        self,
        video_id: int,
        *,
        duration_seconds: int | None,
        width: int | None,
        height: int | None,
        now: datetime | None = None,
    ) -> None:
        """Écrit les métadonnées extraites par ffprobe (durée, dimensions)."""
        self._db.execute(
            _UPDATE_METADATA_SQL,
            (duration_seconds, width, height, now or _utcnow(), video_id),
        )

    def mark_ready(
        self,
        video_id: int,
        *,
        mp4_path: str,
        poster_path: str | None,
        now: datetime | None = None,
    ) -> None:
        """Passe la vidéo en ``ready`` avec ses chemins de sortie (efface l'erreur)."""
        self._db.execute(
            _MARK_READY_SQL,
            (STATUS_READY, mp4_path, poster_path, now or _utcnow(), video_id),
        )

    def list_recent(self, limit: int = 50) -> list[dict]:
        return self._db.fetch_all(_SELECT_RECENT_SQL, (int(limit),))

    def list_by_status(self, status: str, limit: int = 100) -> list[dict]:
        return self._db.fetch_all(_SELECT_BY_STATUS_SQL, (status, int(limit)))
