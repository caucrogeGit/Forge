# pyright: strict
"""API de consultation admin simple des événements statistiques Forge."""

from __future__ import annotations

import json
from typing import Any, Callable, Iterable, cast

from .events import KIND_ACTION, StatsEventError, validate_event_name
from .schema import STATS_EVENTS_TABLE

_DEFAULT_LIMIT = 50
_MAX_LIMIT = 500
_REQUIRED_COLUMNS = ("id", "name", "label", "category", "metadata", "created_at")


class StatsAdminError(ValueError):
    pass


def _validate_limit(limit: int) -> int:
    if not isinstance(limit, int) or isinstance(limit, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsAdminError(
            f"limit doit être un entier, reçu : {type(limit).__name__}."
        )
    if limit < 1:
        raise StatsAdminError(f"limit doit être ≥ 1, reçu : {limit}.")
    return min(limit, _MAX_LIMIT)


def get_stats_events_admin_sql(
    name: str | None = None,
    category: str | None = None,
    limit: int = _DEFAULT_LIMIT,
    kind: str | None = None,
) -> str:
    """Return the SELECT SQL for listing stats events with optional filters.

    La borne appartient au **dialecte** : T-SQL ne connaît pas `LIMIT` et
    exige `OFFSET ... FETCH NEXT`. Écrite en dur, elle rendait cette lecture
    inutilisable sur SQL Server, défaut trouvé en élargissant le relevé de
    portabilité DML aux paquets qu'il ne couvrait pas
    (`OPTIN-DML-PORTABILITY-WIDEN-001`). `forge-mvc-audit` employait déjà
    `limit_clause()` au même endroit.
    """
    from core.database.backend import get_backend

    parts = [
        f"SELECT id, name, label, category, metadata, kind, created_at"
        f" FROM {STATS_EVENTS_TABLE}"
        f" WHERE 1 = 1",
    ]
    if name is not None:
        parts.append(" AND name = ?")
    if category is not None:
        parts.append(" AND category = ?")
    if kind is not None:
        parts.append(" AND kind = ?")
    parts.append(" ORDER BY created_at DESC, id DESC")
    parts.append(get_backend().dialect.limit_clause())
    return "".join(parts)


def prepare_stats_events_admin_params(
    name: str | None = None,
    category: str | None = None,
    limit: int = _DEFAULT_LIMIT,
    kind: str | None = None,
) -> tuple[Any, ...]:
    """Return the SQL parameter tuple for a stats events query."""
    if name is not None:
        try:
            name = validate_event_name(name)
        except StatsEventError as exc:
            raise StatsAdminError(str(exc)) from exc
    if category is not None:
        if not isinstance(category, str) or not category.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            raise StatsAdminError(
                "category doit être une chaîne non vide."
            )
        category = category.strip()
    effective_limit = _validate_limit(limit)
    params: list[Any] = []
    if name is not None:
        params.append(name)
    if category is not None:
        params.append(category)
    if kind is not None:
        # Vocabulaire fermé : un type inventé ne rendrait aucune ligne, et un
        # filtre qui rend zéro sans motif fait chercher le défaut ailleurs.
        from forge_mvc_stats.events import EVENT_KINDS

        valeur = str(kind).strip().lower()
        if valeur not in EVENT_KINDS:
            raise StatsAdminError(
                f"kind invalide : {kind!r}. Valeurs autorisées : "
                f"{', '.join(sorted(EVENT_KINDS))}."
            )
        params.append(valeur)
    params.append(effective_limit)
    return tuple(params)


def normalize_stats_event_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw DB row into a clean stats event dict.

    metadata is deserialized from JSON string to dict.
    Missing required columns or invalid JSON raises StatsAdminError.
    """
    if not isinstance(row, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsAdminError(
            f"Une ligne dict est attendue, reçu : {type(row).__name__}."
        )
    missing = [col for col in _REQUIRED_COLUMNS if col not in row]
    if missing:
        raise StatsAdminError(
            f"Colonnes manquantes dans la ligne : {', '.join(missing)}."
        )
    raw_metadata = row["metadata"]
    if raw_metadata is None or raw_metadata == "":
        metadata: dict[str, Any] = {}
    elif isinstance(raw_metadata, dict):
        metadata = cast("dict[str, Any]", raw_metadata)
    elif isinstance(raw_metadata, str):
        try:
            parsed = json.loads(raw_metadata)
        except json.JSONDecodeError as exc:
            raise StatsAdminError(
                f"metadata JSON invalide : {exc}"
            ) from exc
        if not isinstance(parsed, dict):
            raise StatsAdminError(
                "metadata JSON doit représenter un objet, "
                f"reçu : {type(parsed).__name__}."
            )
        metadata = cast("dict[str, Any]", parsed)
    else:
        raise StatsAdminError(
            f"metadata doit être une chaîne JSON ou None, "
            f"reçu : {type(raw_metadata).__name__}."
        )
    return {
        "id": row["id"],
        "name": row["name"],
        "label": row["label"],
        "category": row["category"],
        "metadata": metadata,
        # Absent des lignes écrites avant `STATS-EVENT-KIND-001`, et des
        # doubles de test qui ne le posent pas : le défaut du contrat vaut
        # mieux qu'une clé manquante que l'affichage devrait deviner.
        "kind": row.get("kind") or KIND_ACTION,
        "created_at": row["created_at"],
    }


def list_stats_events(
    fetch_all: Callable[[str, tuple[Any, ...]], Iterable[dict[str, Any]]],
    name: str | None = None,
    category: str | None = None,
    limit: int = _DEFAULT_LIMIT,
    kind: str | None = None,
) -> list[dict[str, Any]]:
    """List stats events from the database using the provided fetch_all executor.

    Returns a list of normalized dicts. The caller must supply fetch_all —
    Forge never accesses the database automatically.

    `kind` filtre sur le vocabulaire fermé des types d'événement. Ni le filtre
    ni la **colonne** n'existaient ici : la requête ne sélectionnait pas `kind`,
    si bien qu'un écran d'administration ne pouvait ni distinguer une vue de
    page d'une action, ni l'afficher (`STATS-KIND-API-COMPLETENESS-001`).
    """
    sql = get_stats_events_admin_sql(
        name=name, category=category, limit=limit, kind=kind
    )
    params = prepare_stats_events_admin_params(
        name=name, category=category, limit=limit, kind=kind
    )
    rows = fetch_all(sql, params)
    return [normalize_stats_event_row(row) for row in rows]
