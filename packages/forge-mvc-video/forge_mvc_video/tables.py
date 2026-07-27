# pyright: strict
"""Table des vidéos, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge video:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).

Note de précision : les horodatages étaient déclarés `DATETIME(6)` en MariaDB.
Le rendu emploie le type datetime du dialecte, qui perd la microseconde sur
MariaDB seul ; PostgreSQL et SQL Server la conservent.
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition, UniqueConstraint

__all__ = ["VIDEOS", "MIGRATIONS"]

VIDEOS = TableDefinition(
    name="videos",
    columns=[
        Column("id", "identity"),
        Column("uuid", "char", length=36),
        Column("title", "string", length=255, nullable=True),
        Column("original_path", "string", length=500),
        Column("mp4_path", "string", length=500, nullable=True),
        Column("poster_path", "string", length=500, nullable=True),
        Column("mime_type", "string", length=120, nullable=True),
        Column("size_bytes", "big_integer"),
        Column("duration_seconds", "integer", nullable=True),
        Column("width", "integer", nullable=True),
        Column("height", "integer", nullable=True),
        Column("status", "string", length=30),
        Column("error_message", "text", nullable=True),
        Column("created_at", "datetime"),
        Column("updated_at", "datetime"),
    ],
    primary_key=["id"],
    unique_constraints=[UniqueConstraint("uq_videos_uuid", "uuid")],
    indexes=[Index("idx_videos_status", "status")],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260601120000_create_videos.sql", VIDEOS),
]
