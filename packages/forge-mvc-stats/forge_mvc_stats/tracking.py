# pyright: strict
"""Helper Python explicite de tracking statistique pour Forge."""

from __future__ import annotations

import json
from typing import Any, Callable

from .events import StatsEvent, StatsEventError, make_event, validate_event
from .schema import STATS_EVENTS_TABLE

_INSERT_SQL = (
    f"INSERT INTO {STATS_EVENTS_TABLE}"
    " (name, label, category, metadata)"
    " VALUES (?, ?, ?, ?)"
)


def get_track_event_sql() -> str:
    """Return the INSERT SQL for recording a stats event."""
    return _INSERT_SQL


def _serialize_metadata(metadata: dict[str, Any]) -> str:
    try:
        return json.dumps(metadata, ensure_ascii=False, sort_keys=True)
    except (TypeError, ValueError) as exc:
        raise StatsEventError(
            f"metadata non sérialisable en JSON : {exc}"
        ) from exc


def prepare_track_event_values(event: StatsEvent) -> tuple[str, str, str, str]:
    """Return the SQL parameter tuple for a StatsEvent."""
    if not isinstance(event, StatsEvent):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsEventError(
            f"Un StatsEvent est attendu, reçu : {type(event).__name__}."
        )
    return (
        event.name,
        event.label,
        event.category,
        _serialize_metadata(event.metadata),
    )


def track_event(
    execute: Callable[[str, tuple[Any, ...]], Any],
    event_or_name: StatsEvent | str,
    label: str = "",
    category: str = "general",
    metadata: dict[str, Any] | None = None,
) -> StatsEvent:
    """Record a stats event by calling the provided SQL executor.

    The executor must be callable as execute(sql, params).
    Forge never calls this automatically — the developer must call it explicitly.
    """
    if isinstance(event_or_name, StatsEvent):
        event = validate_event(event_or_name)
    elif isinstance(event_or_name, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        event = make_event(
            name=event_or_name,
            label=label,
            category=category,
            metadata=metadata,
        )
    else:
        raise StatsEventError(
            "event_or_name doit être un StatsEvent ou un nom d'événement, "
            f"reçu : {type(event_or_name).__name__}."
        )
    execute(get_track_event_sql(), prepare_track_event_values(event))
    return event
