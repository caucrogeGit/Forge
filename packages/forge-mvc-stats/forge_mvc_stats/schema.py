# pyright: strict
"""Définition SQL générique de la table d'événements statistiques Forge."""

from __future__ import annotations

from core.database.table_ddl import Column, Index, TableDefinition, render_create_table

STATS_EVENTS_TABLE = "forge_stats_events"

STATS_EVENTS_COLUMNS = (
    "id",
    "name",
    "label",
    "category",
    "metadata",
    "created_at",
)

STATS_EVENTS = TableDefinition(
    name="forge_stats_events",
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


def get_stats_events_schema_sql() -> str:
    """Return the SQL CREATE TABLE statement for forge_stats_events."""
    from core.database.backend import get_backend

    return "\n".join(render_create_table(STATS_EVENTS, get_backend().dialect))
