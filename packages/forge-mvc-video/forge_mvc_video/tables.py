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

__all__ = ["VIDEOS", "VIDEO_SUBTITLES", "MIGRATIONS"]

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

# VIDEO-SUBTITLES-001 : une table plutôt qu'une colonne `subtitles_path`.
# Une vidéo porte souvent plusieurs pistes, une par langue, et une colonne
# unique aurait forcé à en choisir une ou à sérialiser une liste dans du texte,
# ce que le principe 5 refuse (le SQL doit rester lisible et interrogeable).
VIDEO_SUBTITLES = TableDefinition(
    name="video_subtitles",
    columns=[
        Column("id", "identity"),
        Column("video_id", "integer"),
        # Étiquette de langue BCP 47, « fr », « en-GB ». Bornée court : elle
        # part dans l'attribut srclang d'une balise track.
        Column("lang", "string", length=35),
        # Ce que le lecteur affiche dans son menu de pistes.
        Column("label", "string", length=120, nullable=True),
        Column("path", "string", length=500),
        # Piste proposée par défaut par le lecteur. Une seule par vidéo, ce que
        # l'application fait respecter : la base ne peut pas exprimer
        # « au plus un vrai par video_id » de façon portable sur les quatre
        # backends, un index partiel n'existant pas partout.
        Column("is_default", "boolean", default=False),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
    unique_constraints=[
        # Deux pistes de même langue pour une vidéo désigneraient la même entrée
        # dans le menu du lecteur.
        UniqueConstraint("uq_video_subtitles_lang", ("video_id", "lang")),
    ],
    indexes=[Index("idx_video_subtitles_video", "video_id")],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260601120000_create_videos.sql", VIDEOS),
    ("20260902100000_create_video_subtitles.sql", VIDEO_SUBTITLES),
]
