# pyright: strict
"""Helper Python explicite de tracking statistique pour Forge."""

from __future__ import annotations

import json
from typing import Any, Callable

from .events import KIND_ACTION, StatsEvent, StatsEventError, make_event, validate_event
from .schema import STATS_EVENTS_TABLE

_INSERT_SQL = (
    f"INSERT INTO {STATS_EVENTS_TABLE}"
    " (name, label, category, metadata, kind)"
    " VALUES (?, ?, ?, ?, ?)"
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


def prepare_track_event_values(event: StatsEvent) -> tuple[str, str, str, str, str]:
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
        event.kind,
    )


#: Marque « argument non fourni », pour distinguer un défaut d'une valeur posée.
_ABSENT: Any = object()


def track_event(
    execute: Callable[[str, tuple[Any, ...]], Any],
    event_or_name: StatsEvent | str,
    label: str = _ABSENT,
    category: str = _ABSENT,
    metadata: dict[str, Any] | None = _ABSENT,
    kind: str = _ABSENT,
) -> StatsEvent:
    """Record a stats event by calling the provided SQL executor.

    The executor must be callable as execute(sql, params).
    Forge never calls this automatically — the developer must call it explicitly.

    `kind` manquait alors que `StatsEvent` le porte depuis
    `STATS-EVENT-KIND-001` (`STATS-KIND-API-COMPLETENESS-001`). Cette fonction
    étant la porte documentée, toute vue de page suivie par le chemin documenté
    était enregistrée comme une **action**.

    Un `StatsEvent` déjà construit porte sa propre forme. Lui joindre `label`,
    `category`, `metadata` ou `kind` est refusé : ces arguments étaient
    auparavant **ignorés en silence**, si bien qu'un appelant croyait poser une
    vue de page et écrivait une action.

    Raises:
        StatsEventError: un `StatsEvent` est accompagné d'arguments de forme,
            ou `event_or_name` n'est ni l'un ni l'autre.
    """
    if isinstance(event_or_name, StatsEvent):
        surnumeraires = [
            nom for nom, valeur in (
                ("label", label), ("category", category),
                ("metadata", metadata), ("kind", kind),
            )
            if valeur is not _ABSENT
        ]
        if surnumeraires:
            raise StatsEventError(
                f"Un StatsEvent porte déjà sa forme : {', '.join(surnumeraires)} "
                "n'a pas d'effet ici. Posez la valeur dans le StatsEvent, ou "
                "passez un nom d'événement."
            )
        event = validate_event(event_or_name)
    elif isinstance(event_or_name, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        event = make_event(
            name=event_or_name,
            label="" if label is _ABSENT else label,
            category="general" if category is _ABSENT else category,
            metadata=None if metadata is _ABSENT else metadata,
            kind=KIND_ACTION if kind is _ABSENT else kind,
        )
    else:
        raise StatsEventError(
            "event_or_name doit être un StatsEvent ou un nom d'événement, "
            f"reçu : {type(event_or_name).__name__}."
        )
    execute(get_track_event_sql(), prepare_track_event_values(event))
    return event
