# pyright: strict
"""Définition SQL générique de la table d'événements statistiques Forge.

La déclaration elle-même vit dans `tables.py`, emplacement conventionnel où le
provisioning partagé des opt-ins va la chercher (ADR-071). Ce module la
réexporte : ces noms appartiennent à l'API publique du paquet depuis son
origine, et `aggregate.py` s'appuie sur `STATS_EVENTS_TABLE`.
"""

from __future__ import annotations

from core.database.table_ddl import render_create_table
from forge_mvc_stats.tables import (
    STATS_EVENTS,
    STATS_EVENTS_COLUMNS,
    STATS_EVENTS_TABLE,
)

__all__ = [
    "STATS_EVENTS",
    "STATS_EVENTS_TABLE",
    "STATS_EVENTS_COLUMNS",
    "get_stats_events_schema_sql",
]


def get_stats_events_schema_sql() -> str:
    """Return the SQL CREATE TABLE statement for forge_stats_events."""
    from core.database.backend import get_backend

    return "\n".join(render_create_table(STATS_EVENTS, get_backend().dialect))
