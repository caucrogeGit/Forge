# pyright: strict
"""Table des événements statistiques, décrite une fois pour les quatre backends.

`forge mvc stats:init` rend cette description pour le backend installé et écrit
le SQL dans `mvc/migrations/`, où il reste relisible avant
`forge migration:apply` (charte §7, ADR-071).

Ce module est l'emplacement conventionnel de la déclaration, celui que le
provisioning partagé (`cli._support.optin_migrations`) va chercher dans chaque
opt-in adossé à la base. `schema.py` réexporte ces noms, qui appartiennent à
l'API publique du paquet depuis son origine.
"""
from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition

__all__ = ["STATS_EVENTS", "STATS_EVENTS_TABLE", "STATS_EVENTS_COLUMNS", "MIGRATIONS"]

#: Nom de la table d'événements.
STATS_EVENTS_TABLE = "forge_stats_events"

#: Colonnes de la table, dans l'ordre de déclaration.
STATS_EVENTS_COLUMNS = (
    "id",
    "name",
    "label",
    "category",
    "metadata",
    "created_at",
)

STATS_EVENTS = TableDefinition(
    name=STATS_EVENTS_TABLE,
    columns=[
        Column("id", "identity"),
        Column("name", "string", length=100),
        Column("label", "string", length=150),
        Column("category", "string", length=100, default="general"),
        Column("metadata", "json", nullable=True),
        Column("created_at", "datetime", default_now=True),
    ],
    primary_key=["id"],
    indexes=[
        Index("idx_forge_stats_events_name", "name"),
        Index("idx_forge_stats_events_category", "category"),
        Index("idx_forge_stats_events_created_at", "created_at"),
    ],
)

#: Migrations livrées par le paquet : (nom de fichier, table décrite).
MIGRATIONS: list[tuple[str, TableDefinition]] = [
    ("20260808130000_create_forge_stats_events.sql", STATS_EVENTS),
]
