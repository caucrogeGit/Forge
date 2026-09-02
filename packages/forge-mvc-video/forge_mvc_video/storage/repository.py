# pyright: strict
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
    "SUBTITLES_TABLE",
]

TABLE = "videos"

STATUS_UPLOADED = "uploaded"
STATUS_PROCESSING = "processing"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
VALID_STATUSES = frozenset({
    STATUS_UPLOADED, STATUS_PROCESSING, STATUS_READY, STATUS_FAILED,
})

# Marqueur de paramètre : `?`, le format de Forge (`VIDEO-DML-PORTABLE-001`).
#
# Ce fichier écrivait `%s`, le format natif du connecteur MariaDB. Le cœur
# traduit `?` vers le format de chaque pilote, et **double tout `%` littéral**
# au passage : sur PostgreSQL, un `%s` déjà écrit devenait donc `%%s`, un texte
# et non un marqueur. Le dépôt vidéo était par là inutilisable sur PostgreSQL
# comme sur SQL Server, tous deux au niveau plein depuis l'ADR-084, avec
# l'erreur « 0 marqueurs pour 8 paramètres ».
_INSERT_SQL = (
    "INSERT INTO videos "
    "(uuid, title, original_path, size_bytes, mime_type, status, "
    "created_at, updated_at) "
    "VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
)
_SELECT_BY_UUID_SQL = "SELECT * FROM videos WHERE uuid = ?"
_SELECT_BY_ID_SQL = "SELECT * FROM videos WHERE id = ?"
_UPDATE_STATUS_SQL = (
    "UPDATE videos SET status = ?, error_message = ?, updated_at = ? "
    "WHERE id = ?"
)
_UPDATE_METADATA_SQL = (
    "UPDATE videos SET duration_seconds = ?, width = ?, height = ?, "
    "updated_at = ? WHERE id = ?"
)
_MARK_READY_SQL = (
    "UPDATE videos SET status = ?, mp4_path = ?, poster_path = ?, "
    "error_message = NULL, updated_at = ? WHERE id = ?"
)
_DELETE_SQL = "DELETE FROM videos WHERE id = ?"
_SELECT_ALL_PATHS_SQL = "SELECT original_path, mp4_path, poster_path FROM videos"

# VIDEO-QUOTA-001 : totaux de la vidéothèque. `COALESCE` parce qu'une table
# vide rend NULL et non zéro sur les quatre backends, et qu'un NULL propagé
# ferait passer le premier envoi pour un dépassement.
_SELECT_TOTALS_SQL = (
    "SELECT COUNT(*) AS videos, "
    "COALESCE(SUM(size_bytes), 0) AS total_bytes, "
    "COALESCE(SUM(duration_seconds), 0) AS total_duration "
    "FROM videos"
)

# VIDEO-SUBTITLES-001
SUBTITLES_TABLE = "video_subtitles"
_INSERT_SUBTITLE_SQL = (
    "INSERT INTO video_subtitles (video_id, lang, label, path, is_default, created_at) "
    "VALUES (?, ?, ?, ?, ?, ?)"
)
_SELECT_SUBTITLES_SQL = (
    "SELECT id, video_id, lang, label, path, is_default, created_at "
    "FROM video_subtitles WHERE video_id = ? ORDER BY lang"
)
_SELECT_SUBTITLE_SQL = (
    "SELECT id, video_id, lang, label, path, is_default, created_at "
    "FROM video_subtitles WHERE video_id = ? AND lang = ?"
)
_DELETE_SUBTITLE_SQL = "DELETE FROM video_subtitles WHERE video_id = ? AND lang = ?"
_DELETE_SUBTITLES_SQL = "DELETE FROM video_subtitles WHERE video_id = ?"
_CLEAR_DEFAULT_SQL = "UPDATE video_subtitles SET is_default = ? WHERE video_id = ?"


def _limit_clause() -> str:
    """Borne du backend actif : T-SQL ne connaît pas `LIMIT`.

    Les deux listes l'écrivaient en dur, ce qui les cassait sur SQL Server même
    une fois les marqueurs corrigés. La clause exige un `ORDER BY`, que les deux
    requêtes portent déjà.
    """
    from core.database.backend import get_backend

    return get_backend().dialect.limit_clause()


def _select_recent_sql() -> str:
    return f"SELECT * FROM videos ORDER BY id DESC{_limit_clause()}"


def _select_by_status_sql() -> str:
    return f"SELECT * FROM videos WHERE status = ? ORDER BY id ASC{_limit_clause()}"


class DbAdapter(Protocol):
    """Interface attendue, conforme à ``core.database.db``."""

    def insert(self, sql: str, params: tuple[Any, ...]) -> int:  # pragma: no cover - protocole
        ...

    def execute(self, sql: str, params: tuple[Any, ...]) -> Any:  # pragma: no cover - protocole
        ...

    def fetch_one(self, sql: str, params: tuple[Any, ...]) -> dict[str, Any] | None:  # pragma: no cover - protocole
        ...

    def fetch_all(self, sql: str, params: tuple[Any, ...]) -> list[dict[str, Any]]:  # pragma: no cover - protocole
        ...


def _default_db_adapter() -> DbAdapter:
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

    def get_by_uuid(self, uuid: str) -> dict[str, Any] | None:
        return self._db.fetch_one(_SELECT_BY_UUID_SQL, (uuid,))

    def get_by_id(self, video_id: int) -> dict[str, Any] | None:
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

    def list_recent(self, limit: int = 50) -> list[dict[str, Any]]:
        return self._db.fetch_all(_select_recent_sql(), (int(limit),))

    def list_by_status(self, status: str, limit: int = 100) -> list[dict[str, Any]]:
        return self._db.fetch_all(_select_by_status_sql(), (status, int(limit)))

    def delete(self, video_id: int) -> None:
        """Supprime une ligne ``videos`` (utilisé par ``video:cleanup``)."""
        self._db.execute(_DELETE_SQL, (int(video_id),))

    def totals(self) -> "dict[str, int]":
        """Nombre de vidéos, octets et secondes cumulés (`VIDEO-QUOTA-001`).

        La durée n'est connue qu'après le sondage : une vidéo envoyée mais pas
        encore traitée compte pour zéro seconde, et pour sa taille entière.
        """
        row = self._db.fetch_one(_SELECT_TOTALS_SQL, ())
        if row is None:
            return {"videos": 0, "total_bytes": 0, "total_duration": 0}
        return {
            "videos": int(row.get("videos") or 0),
            "total_bytes": int(row.get("total_bytes") or 0),
            "total_duration": int(row.get("total_duration") or 0),
        }

    # --- Sous-titres (VIDEO-SUBTITLES-001) ---------------------------------

    def add_subtitle(
        self,
        video_id: int,
        *,
        lang: str,
        path: str,
        label: "str | None" = None,
        is_default: bool = False,
        now: "datetime | None" = None,
    ) -> int:
        """Enregistre une piste. Une seule peut être la piste par défaut.

        Poser une nouvelle piste par défaut retire le drapeau des autres : deux
        pistes par défaut laisseraient le lecteur en choisir une, et laquelle
        dépendrait du navigateur.
        """
        moment = now or _utcnow()
        if is_default:
            self._db.execute(_CLEAR_DEFAULT_SQL, (False, video_id))
        return self._db.insert(
            _INSERT_SUBTITLE_SQL,
            (video_id, lang, label, path, is_default, moment),
        )

    def list_subtitles(self, video_id: int) -> "list[dict[str, Any]]":
        return self._db.fetch_all(_SELECT_SUBTITLES_SQL, (video_id,))

    def get_subtitle(self, video_id: int, lang: str) -> "dict[str, Any] | None":
        return self._db.fetch_one(_SELECT_SUBTITLE_SQL, (video_id, lang))

    def delete_subtitle(self, video_id: int, lang: str) -> None:
        self._db.execute(_DELETE_SUBTITLE_SQL, (video_id, lang))

    def delete_subtitles(self, video_id: int) -> None:
        """Retire toutes les pistes d'une vidéo, à sa suppression."""
        self._db.execute(_DELETE_SUBTITLES_SQL, (video_id,))

    def all_relpaths(self) -> set[str]:
        """Tous les chemins relatifs référencés (original/mp4/poster).

        Sert au garbage-collector ``video:cleanup --orphan-files`` : un fichier
        du stockage absent de cet ensemble est considéré orphelin.
        """
        paths: set[str] = set()
        for row in self._db.fetch_all(_SELECT_ALL_PATHS_SQL, ()):
            for key in ("original_path", "mp4_path", "poster_path"):
                value = row.get(key)
                if value:
                    paths.add(value)
        return paths
