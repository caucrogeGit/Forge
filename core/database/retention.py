# pyright: strict
"""Borne de rétention partagée par les opt-ins adossés à la base.

Trois opt-ins purgent une table par âge, et le calcul de la borne était écrit
deux fois à l'identique, dans `forge-mvc-audit` et `forge-mvc-stats`. Le
troisième, `forge-mvc-iot`, allait en produire une troisième copie
(`IOT-RETENTION-GC-001`). La cause est retirée ici plutôt que recopiée, comme
la règle d'évolution A le demande.

La borne se calcule en Python et part en **paramètre lié**, jamais en
expression SQL de date. Aucun dialecte n'entre donc dans la requête de purge,
ce qui la rend portable sans effort sur les quatre backends. Le motif inverse a
un coût mesuré, voir l'audit `OPTIN-DML-DIALECT-001`, où un `NOW()` écrit en
dur rendait la DML inutilisable ailleurs que sur MariaDB.

Les erreurs sont des `ValueError`. Un opt-in qui expose un type d'erreur propre
l'enveloppe, ce que font `forge-mvc-audit` et `forge-mvc-stats` pour ne pas
rompre leur API publique.
"""
from __future__ import annotations

from datetime import datetime, timedelta

from core.database.timestamps import utc_now

__all__ = ["DATETIME_FMT", "cutoff_for_days"]

#: Format d'horodatage des bornes, commun à Forge.
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"


def cutoff_for_days(
    keep_days: int, *, now: datetime | None = None, quoi: str = "la table"
) -> str:
    """Borne de rétention : l'instant, en UTC, `keep_days` jours dans le passé.

    `quoi` nomme ce qui serait vidé, pour que le message d'erreur parle de la
    table de l'appelant et non d'une abstraction.

    Raises:
        ValueError: `keep_days` n'est pas un entier, ou est inférieur à 1. Une
            rétention nulle ou négative viderait tout, ce qui ne peut pas être
            le résultat d'une étourderie de frappe.
    """
    if not isinstance(keep_days, int) or isinstance(keep_days, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError(f"keep_days doit être un entier. Reçu : {keep_days!r}.")
    if keep_days < 1:
        raise ValueError(
            f"keep_days doit être >= 1. Reçu : {keep_days}. "
            f"Une rétention nulle ou négative viderait {quoi}."
        )
    instant = now if now is not None else utc_now()
    return (instant - timedelta(days=keep_days)).strftime(DATETIME_FMT)
