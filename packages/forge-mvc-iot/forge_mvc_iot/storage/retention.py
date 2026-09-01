# pyright: strict
"""Rétention de la table de mesures IoT (IOT-RETENTION-GC-001).

`iot_events` reçoit une ligne par mesure publiée et rien ne la bornait. Un
capteur qui émet toutes les dix secondes y dépose plus de trois millions de
lignes par an, et un site en compte rarement un seul. La table grossissait donc
sans fin, jusqu'à la panne de remplissage, alors que `sessions:gc`, `audit:gc`
et `stats:gc` avaient posé le précédent.

Ce module suit la convention du paquet et n'accède jamais à la base de
lui-même : il rend du SQL et calcule des paramètres, l'appelant fournit
l'exécuteur, comme le fait `repository.py`. La commande `forge iot:gc` fait la
jonction.

La borne vient de `core.database.retention`, partagée avec les deux autres
opt-ins qui purgent par âge. Elle part en paramètre lié, jamais en expression
SQL de date : aucun dialecte n'entre dans la requête, ce qui la rend portable
sur les quatre backends sans effort.

La purge est indexée : `idx_iot_events_received_at` porte déjà sur la colonne
filtrée, si bien qu'aucune migration n'est requise.
"""
from __future__ import annotations

from datetime import datetime

from core.database.retention import DATETIME_FMT, cutoff_for_days as _cutoff_for_days

from forge_mvc_iot.tables import IOT_EVENTS

__all__ = [
    "IotRetentionError",
    "DATETIME_FMT",
    "cutoff_for_days",
    "get_iot_count_before_sql",
    "get_iot_purge_sql",
]


class IotRetentionError(ValueError):
    """Rétention invalide, ou borne inexploitable."""


def cutoff_for_days(keep_days: int, *, now: datetime | None = None) -> str:
    """Borne de rétention : l'instant, en UTC, `keep_days` jours dans le passé.

    Lève :class:`IotRetentionError` si `keep_days` est inférieur à 1 : une
    rétention nulle ou négative viderait toute la table de mesures, ce qui ne
    peut pas être le résultat d'une étourderie de frappe.
    """
    try:
        return _cutoff_for_days(keep_days, now=now, quoi="toute la table de mesures")
    except ValueError as exc:
        raise IotRetentionError(str(exc)) from exc


def get_iot_count_before_sql() -> str:
    """SQL du comptage des mesures antérieures à une borne."""
    return f"SELECT COUNT(*) AS total FROM {IOT_EVENTS.name} WHERE received_at < ?"


def get_iot_purge_sql() -> str:
    """SQL de la suppression des mesures antérieures à une borne.

    Aucune archive n'est produite avant suppression : un exploitant tenu de
    conserver ses mesures doit les exporter lui-même, en amont.
    """
    return f"DELETE FROM {IOT_EVENTS.name} WHERE received_at < ?"
