# pyright: strict
"""Table de les notifications in-app, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge notifications:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["NOTIFICATIONS", "MIGRATIONS"]

NOTIFICATIONS = TableDefinition(
    name="notifications",
    columns=[
        Column("id", "identity"),
        Column("recipient", "string", length=191),
        Column("type", "string", length=64, default="info"),
        Column("message", "text"),
        Column("data", "text"),
        Column("read_at", "datetime", nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
    indexes=[
        Index("idx_notif_recipient", ("recipient", "read_at")),
        Index("idx_notif_created", "created_at"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260626150000_create_notifications.sql", NOTIFICATIONS),
]
