# pyright: strict
"""Table des événements IoT, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge iot:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).

Note de précision : `received_at` était déclaré `DATETIME(6)` en MariaDB. Le
rendu emploie le type datetime du dialecte, qui perd la microseconde sur
MariaDB seul ; PostgreSQL et SQL Server la conservent. L'ordre des événements
reçus dans la même seconde reste départagé par la clé primaire croissante.
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["IOT_EVENTS", "MIGRATIONS"]

IOT_EVENTS = TableDefinition(
    name="iot_events",
    columns=[
        Column("id", "identity"),
        Column("site", "string", length=64),
        Column("device_id", "string", length=64),
        Column("kind", "string", length=64),
        Column("value", "float"),
        Column("unit", "string", length=32),
        Column("timestamp", "string", length=40),
        Column("metadata_json", "text", nullable=True),
        Column("received_at", "datetime"),
    ],
    primary_key=["id"],
    indexes=[
        Index("idx_iot_events_site_device", ("site", "device_id")),
        Index("idx_iot_events_received_at", "received_at"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260528120000_create_iot_events.sql", IOT_EVENTS),
]
