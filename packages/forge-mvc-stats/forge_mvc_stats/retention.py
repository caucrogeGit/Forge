# pyright: strict
"""Rétention de la table d'événements statistiques (STATS-RETENTION-001).

`forge_stats_events` reçoit une ligne par événement suivi et rien ne la bornait.
Une application qui trace consciencieusement y accumule des millions de lignes,
et les agrégats de `aggregate.py` ralentissent d'autant, sans que rien ne
prévienne.

Ce module suit la convention du paquet et non celle de `forge-mvc-audit` : il
n'accède **jamais** à la base de lui-même. Il rend du SQL et calcule des
paramètres, l'appelant fournit l'exécuteur, exactement comme `track_event` et
`count_stats_events`. La commande `forge stats:gc` fait la jonction avec
`core.database`.

La borne est calculée en Python et part en **paramètre lié**, jamais en
expression SQL de date. Aucun dialecte n'entre donc dans la requête, ce qui la
rend portable sans effort sur les quatre backends. Le motif inverse a un coût
mesuré, voir l'audit `OPTIN-DML-DIALECT-001`.
"""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

from core.database.retention import DATETIME_FMT as _DATETIME_FMT
from core.database.retention import cutoff_for_days as _cutoff_for_days

from forge_mvc_stats.tables import STATS_EVENTS_TABLE

__all__ = [
    "StatsRetentionError",
    "DATETIME_FMT",
    "cutoff_for_days",
    "get_stats_purge_sql",
    "get_stats_count_before_sql",
    "purge_stats_events_before",
    "count_stats_events_before",
]


class StatsRetentionError(ValueError):
    """Rétention invalide, ou borne inexploitable."""


#: Format d'horodatage des bornes, commun à Forge. Alias du cœur.
DATETIME_FMT = _DATETIME_FMT


def cutoff_for_days(keep_days: int, *, now: datetime | None = None) -> str:
    """Borne de rétention : l'instant, en UTC, `keep_days` jours dans le passé.

    Lève :class:`StatsRetentionError` si `keep_days` est inférieur à 1 : une
    rétention nulle ou négative viderait la table entière, ce qui ne peut pas
    être le résultat d'une étourderie de frappe.
    """
    # Le calcul vit dans le cœur (`IOT-RETENTION-GC-001`) : il était écrit à
    # l'identique ici et dans `forge-mvc-audit`. `StatsRetentionError` reste le
    # type public de ce paquet, d'où l'enveloppe.
    try:
        return _cutoff_for_days(keep_days, now=now, quoi="toute la table d'événements")
    except ValueError as exc:
        raise StatsRetentionError(str(exc)) from exc


def get_stats_count_before_sql() -> str:
    """SQL du comptage des événements antérieurs à une borne."""
    return f"SELECT COUNT(*) AS total FROM {STATS_EVENTS_TABLE} WHERE created_at < ?"


def get_stats_purge_sql() -> str:
    """SQL de la suppression des événements antérieurs à une borne.

    La suppression est indexée, `idx_forge_stats_events_created_at` portant déjà
    sur `created_at`. Aucune migration n'est requise par la rétention.
    """
    return f"DELETE FROM {STATS_EVENTS_TABLE} WHERE created_at < ?"


def _validate_cutoff(cutoff: str) -> str:
    if not isinstance(cutoff, str) or not cutoff.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsRetentionError("cutoff doit être une chaîne non vide (horodatage).")
    return cutoff.strip()


def count_stats_events_before(
    fetch_one: Callable[[str, tuple[Any, ...]], "dict[str, Any] | None"],
    cutoff: str,
) -> int:
    """Nombre d'événements antérieurs à `cutoff`, sans rien supprimer.

    Sert à montrer l'effet avant de l'appliquer : `forge stats:gc` affiche ce
    compte par défaut et n'efface qu'avec `--run` (charte §7).
    """
    row = fetch_one(get_stats_count_before_sql(), (_validate_cutoff(cutoff),))
    return int(row["total"]) if row else 0


def purge_stats_events_before(
    execute: Callable[[str, tuple[Any, ...]], Any],
    cutoff: str,
) -> int:
    """Supprime les événements antérieurs à `cutoff`. Retourne le nombre supprimé.

    Aucun agrégat de remplacement n'est calculé avant suppression : purger des
    événements détruit de l'information, et l'exploitant qui veut conserver des
    totaux doit les calculer en amont, par `count_stats_events`.
    """
    return int(execute(get_stats_purge_sql(), (_validate_cutoff(cutoff),)))
