# pyright: strict
"""Table de les paramètres applicatifs, décrite une fois pour les quatre backends.

Remplace le fichier SQL figé que ce paquet livrait, inexécutable ailleurs que
sur MariaDB (audit `OPTIN-DDL-DIALECT-AUDIT-001`). `forge settings:init` rend
désormais cette description pour le backend installé et écrit le SQL dans
`mvc/migrations/`, où il reste relisible avant `forge migration:apply`
(charte §7, ADR-071).
"""
from __future__ import annotations

from core.database.table_ddl import Column, TableDefinition

__all__ = ["APP_SETTINGS", "MIGRATIONS"]

APP_SETTINGS = TableDefinition(
    name="app_settings",
    columns=[
        Column("setting_key", "string", length=191),
        Column("setting_value", "text"),
        Column("value_type", "string", length=16, default="str"),
        # `on_update_now` n'est honoré que par les dialectes qui le connaissent
        # (MariaDB) ; ailleurs le simple DEFAULT est rendu et l'application
        # pose la date, comme le store le fait déjà.
        Column("updated_at", "datetime", default_now=True, on_update_now=True),
    ],
    primary_key=["setting_key"],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260626120000_create_app_settings.sql", APP_SETTINGS),
]
