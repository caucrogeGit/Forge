# pyright: strict
"""Agrégation par comptage des événements statistiques (ADR-037).

Compte les événements groupés par une dimension catégorielle (`name` ou
`category`), avec filtres optionnels (`name`, `category`, `since`). Le SQL reste
visible et 100 % paramétré ; la **colonne de regroupement n'est jamais une
chaîne libre** : elle est résolue via une liste blanche fermée, ce qui exclut
toute injection par nom de colonne. L'exécuteur est injecté par l'application :
le module n'ouvre jamais de connexion.
"""

from __future__ import annotations

from typing import Any, Callable, Iterable

from .events import StatsEventError, validate_event_name
from .schema import STATS_EVENTS_TABLE

# Dimensions de regroupement autorisées → colonne SQL réelle (liste blanche).
# group_by ne provient jamais directement de l'entrée : il est résolu ici.
#
# `day` et `kind` s'y sont ajoutés (`DOC-STATS-AGGREGATES-001`,
# `STATS-EVENT-KIND-001`). Grouper par journée demandait auparavant de
# rapatrier tous les horodatages pour les tronquer en Python, ce que la base
# fait sans rien déplacer.
_GROUP_BY_COLUMNS = {
    "name": "name",
    "category": "category",
    "kind": "kind",
}

#: Dimensions dont l'expression SQL dépend du backend, résolues à l'exécution.
_GROUP_BY_DIALECTAL = {"day"}


class StatsAggregateError(ValueError):
    pass


def _resolve_group_by(group_by: str) -> str:
    """Expression SQL de la dimension demandée, depuis une liste blanche.

    `day` n'est pas une colonne : c'est une expression rendue par le dialecte,
    aucun des quatre backends n'écrivant la troncature d'un horodatage de la
    même façon (`DATE()`, `date()`, `CAST(... AS DATE)`).
    """
    if group_by in _GROUP_BY_DIALECTAL:
        from core.database.backend import get_backend

        return get_backend().dialect.date_expression("created_at")
    column = _GROUP_BY_COLUMNS.get(group_by)
    if column is None:
        autorisees = ", ".join(sorted(set(_GROUP_BY_COLUMNS) | _GROUP_BY_DIALECTAL))
        raise StatsAggregateError(
            f"group_by invalide : {group_by!r}. Valeurs autorisées : {autorisees}."
        )
    return column


def get_stats_counts_sql(
    group_by: str,
    name: str | None = None,
    category: str | None = None,
    since: str | None = None,
    kind: str | None = None,
) -> str:
    """Return the COUNT(*) GROUP BY SQL for the given (whitelisted) dimension."""
    column = _resolve_group_by(group_by)
    parts = [
        f"SELECT {column} AS bucket, COUNT(*) AS total"
        f" FROM {STATS_EVENTS_TABLE}"
        f" WHERE 1 = 1",
    ]
    if name is not None:
        parts.append(" AND name = ?")
    if category is not None:
        parts.append(" AND category = ?")
    if since is not None:
        parts.append(" AND created_at >= ?")
    if kind is not None:
        parts.append(" AND kind = ?")
    parts.append(f" GROUP BY {column}")
    # Une série temporelle se lit dans l'ordre du temps. Trier une courbe par
    # total décroissant la rendrait illisible, et c'est le tri par défaut des
    # autres dimensions, où il classe du plus fréquent au moins fréquent.
    if group_by == "day":
        parts.append(f" ORDER BY {column} ASC")
    else:
        parts.append(" ORDER BY total DESC, bucket ASC")
    return "".join(parts)


def prepare_stats_counts_params(
    group_by: str,
    name: str | None = None,
    category: str | None = None,
    since: str | None = None,
    kind: str | None = None,
) -> tuple[Any, ...]:
    """Return the bound-parameter tuple matching `get_stats_counts_sql`."""
    _resolve_group_by(group_by)  # rejette une dimension invalide aussi côté params
    params: list[Any] = []
    if name is not None:
        try:
            name = validate_event_name(name)
        except StatsEventError as exc:
            raise StatsAggregateError(str(exc)) from exc
        params.append(name)
    if category is not None:
        if not isinstance(category, str) or not category.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            raise StatsAggregateError("category doit être une chaîne non vide.")
        params.append(category.strip())
    if since is not None:
        if not isinstance(since, str) or not since.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            raise StatsAggregateError(
                "since doit être une chaîne non vide (timestamp ISO)."
            )
        params.append(since.strip())
    if kind is not None:
        # Le vocabulaire est fermé : un type inventé ne rendrait aucune ligne,
        # et un filtre qui rend zéro sans motif fait chercher un défaut
        # ailleurs, dans les données ou dans l'écriture des événements.
        from forge_mvc_stats.events import EVENT_KINDS

        valeur = str(kind).strip().lower()
        if valeur not in EVENT_KINDS:
            raise StatsAggregateError(
                f"kind invalide : {kind!r}. Valeurs autorisées : "
                f"{', '.join(sorted(EVENT_KINDS))}."
            )
        params.append(valeur)
    return tuple(params)


def normalize_stats_count_row(row: dict[str, Any]) -> dict[str, Any]:
    """Normalize a raw count row into `{"bucket": ..., "total": int}`."""
    if not isinstance(row, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsAggregateError(
            f"Une ligne dict est attendue, reçu : {type(row).__name__}."
        )
    for col in ("bucket", "total"):
        if col not in row:
            raise StatsAggregateError(f"Colonne manquante dans la ligne : {col}.")
    return {"bucket": row["bucket"], "total": int(row["total"])}


def count_stats_events(
    fetch_all: Callable[[str, tuple[Any, ...]], Iterable[dict[str, Any]]],
    group_by: str,
    name: str | None = None,
    category: str | None = None,
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Count events grouped by `group_by`, using the provided fetch_all executor.

    Returns normalized `{"bucket", "total"}` dicts. The caller supplies
    fetch_all — Forge never accesses the database automatically.
    """
    sql = get_stats_counts_sql(group_by, name=name, category=category, since=since)
    params = prepare_stats_counts_params(
        group_by, name=name, category=category, since=since
    )
    rows = fetch_all(sql, params)
    return [normalize_stats_count_row(row) for row in rows]
