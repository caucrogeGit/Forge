# pyright: strict
"""Table de médias, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge images:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["MEDIA", "MIGRATIONS"]

MEDIA = TableDefinition(
    name="media",
    columns=[
        Column("Id", "identity"),
        Column("EntityName", "string", length=100),
        Column("EntityId", "integer"),
        Column("Path", "string", length=500),
        Column("OriginalName", "string", length=255),
        Column("MimeType", "string", length=120),
        Column("Size", "integer"),
        Column("Role", "string", length=50, default="default"),
        Column("Position", "integer", default=0),
        Column("AltText", "string", length=255, nullable=True),
        Column("CreatedAt", "datetime"),
    ],
    primary_key=["Id"],
    indexes=[Index("idx_media_entity", ("EntityName", "EntityId"))],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260710120000_create_media.sql", MEDIA),
]
