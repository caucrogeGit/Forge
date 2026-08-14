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
        # `on_update_now` est retiré : il n'était honoré que par MariaDB, si
        # bien que la colonne restait figée sur la date de création ailleurs.
        # Le commentaire qui tenait ici affirmait que « le store pose la date,
        # comme il le fait déjà » ; le store ne l'écrivait pas. Il le fait
        # désormais (`SETTINGS-UPDATED-AT-001`), sur les quatre backends.
        #
        # Le DEFAULT reste utile pour une ligne insérée hors du store, par une
        # migration ou à la main.
        Column("updated_at", "datetime", default_now=True),
    ],
    primary_key=["setting_key"],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260626120000_create_app_settings.sql", APP_SETTINGS),
]
