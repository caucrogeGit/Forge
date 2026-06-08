"""Forge stats — événements génériques, schéma SQL, tracking et consultation."""

from __future__ import annotations

from forge_mvc_stats.admin import (
    StatsAdminError,
    get_stats_events_admin_sql,
    list_stats_events,
    normalize_stats_event_row,
    prepare_stats_events_admin_params,
)
from forge_mvc_stats.events import (
    StatsEvent,
    StatsEventError,
    make_event,
    normalize_event_name,
    validate_event,
    validate_event_name,
)
from forge_mvc_stats.schema import (
    STATS_EVENTS_COLUMNS,
    STATS_EVENTS_TABLE,
    get_stats_events_schema_sql,
)
from forge_mvc_stats.tracking import (
    get_track_event_sql,
    prepare_track_event_values,
    track_event,
)

__version__ = "1.0.0b15"

__all__ = [
    "StatsEvent",
    "StatsEventError",
    "normalize_event_name",
    "validate_event_name",
    "make_event",
    "validate_event",
    "STATS_EVENTS_TABLE",
    "STATS_EVENTS_COLUMNS",
    "get_stats_events_schema_sql",
    "get_track_event_sql",
    "prepare_track_event_values",
    "track_event",
    "StatsAdminError",
    "get_stats_events_admin_sql",
    "prepare_stats_events_admin_params",
    "normalize_stats_event_row",
    "list_stats_events",
]
