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

__all__ = ["IOT_EVENTS", "IOT_API_TOKENS", "MIGRATIONS"]

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

# IOT-DEVICE-AUTH-001 : jetons d'accès par site ou par équipement. L'API de
# lecture n'avait qu'un jeton d'environnement, qui ouvrait TOUS les sites : un
# prestataire chargé des capteurs d'un bâtiment lisait par là les mesures des
# autres.
IOT_API_TOKENS = TableDefinition(
    name="iot_api_tokens",
    columns=[
        Column("id", "identity"),
        # Empreinte SHA-256 hexadécimale. Le jeton n'est JAMAIS stocké en clair
        # et n'est affiché qu'une fois, à sa création.
        Column("token_hash", "char", length=64, unique=True),
        # `NULL` désigne la portée globale, tous sites confondus.
        Column("site", "string", length=64, nullable=True),
        # `NULL` avec un site désigne le site entier.
        Column("device_id", "string", length=64, nullable=True),
        # À quoi sert ce jeton, pour que l'exploitant sache lequel révoquer.
        Column("label", "string", length=120, nullable=True),
        Column("created_at", "datetime"),
        # Révocation par date et non par suppression : savoir qu'un jeton a
        # existé, et quand il a cessé de valoir, fait partie de ce qu'un
        # exploitant doit pouvoir retrouver.
        Column("revoked_at", "datetime", nullable=True),
    ],
    primary_key=["id"],
    indexes=[Index("idx_iot_api_tokens_site", ("site", "device_id"))],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260528120000_create_iot_events.sql", IOT_EVENTS),
    ("20260902110000_create_iot_api_tokens.sql", IOT_API_TOKENS),
]
