# pyright: strict
"""Agrégats sur une fenêtre de temps (`IOT-AGGREGATES-001`).

Le paquet savait rendre les mesures brutes et les compter. La question qu'on
pose à des relevés de capteurs n'avait aucune réponse : « quelle a été la
température moyenne de la semaine, et jusqu'où est elle montée ».

L'application devait donc rapatrier toutes les mesures pour les additionner en
Python, ce qui charge en mémoire ce que la base sait faire sans rien déplacer,
et qui devient impraticable dès qu'un capteur relève chaque minute.

## Ce que le module refuse de faire

Il ne **regroupe pas par intervalle**. Une série temporelle par tranches de
cinq minutes demande des fonctions de fenêtrage que les quatre backends
n'écrivent pas de la même façon, et le principe 5 veut du SQL visible plutôt
qu'un générateur qui masquerait quatre dialectes.

Il n'**interpole rien** non plus. Une fenêtre sans mesure rend un agrégat vide,
et non un zéro : « le capteur n'a rien envoyé » et « le capteur a relevé zéro »
sont deux faits différents, que confondre fausserait toute moyenne.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any, Protocol

from forge_mvc_iot.tables import IOT_EVENTS

__all__ = [
    "IotAggregateError",
    "IotAggregate",
    "window_start",
    "select_aggregate_sql",
    "aggregate_for_device",
    "aggregate_for_site",
]

_TABLE = IOT_EVENTS.name

#: Fenêtre maximale acceptée, en heures. Un an. Au delà, la requête balaye la
#: table entière et la question relève d'un export, pas d'une API de lecture.
MAX_WINDOW_HOURS = 24 * 366


class IotAggregateError(ValueError):
    """Fenêtre ou portée invalides."""


@dataclass(frozen=True)
class IotAggregate:
    """Résultat d'un agrégat. `count` à zéro veut dire « aucune mesure »."""

    count: int
    average: "float | None" = None
    minimum: "float | None" = None
    maximum: "float | None" = None
    unit: "str | None" = None

    @property
    def is_empty(self) -> bool:
        """Vrai si la fenêtre ne contient aucune mesure.

        Distinct d'une moyenne nulle : un capteur qui n'a rien envoyé et un
        capteur qui a relevé zéro ne disent pas la même chose.
        """
        return self.count == 0

    def as_dict(self) -> "dict[str, Any]":
        return {
            "count": self.count,
            "average": self.average,
            "min": self.minimum,
            "max": self.maximum,
            "unit": self.unit,
        }


class _DbAdapter(Protocol):
    def fetch_one(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "dict[str, Any] | None": ...


def window_start(hours: int, *, now: "datetime | None" = None) -> datetime:
    """Début de fenêtre, `hours` heures avant l'instant courant, en UTC.

    Raises:
        IotAggregateError: fenêtre nulle, négative, ou au delà d'un an.
    """
    if not isinstance(hours, int) or isinstance(hours, bool):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise IotAggregateError(f"la fenêtre doit être un entier d'heures. Reçu : {hours!r}.")
    if hours <= 0:
        raise IotAggregateError(
            f"la fenêtre doit être strictement positive. Reçu : {hours}."
        )
    if hours > MAX_WINDOW_HOURS:
        raise IotAggregateError(
            f"fenêtre trop large : {hours} heures dépasse {MAX_WINDOW_HOURS}. "
            "Au delà, la question relève d'un export, pas d'une API de lecture."
        )
    instant = now or datetime.now(UTC).replace(tzinfo=None)
    return instant - timedelta(hours=hours)


def select_aggregate_sql(*, by_device: bool) -> str:
    """SQL de l'agrégat, restreint à un site ou à un couple site/équipement.

    `AVG`, `MIN`, `MAX` et `COUNT` sont du SQL standard, écrits une fois pour
    les quatre backends. `COUNT` porte sur `value` et non sur `*` : une mesure
    sans valeur ne doit pas gonfler l'effectif d'une moyenne qu'elle n'alimente
    pas.

    Le SQL reste visible ici, conformément au principe 5.
    """
    filtre = "site = ? AND device_id = ?" if by_device else "site = ?"
    return (
        "SELECT COUNT(value) AS n, AVG(value) AS moyenne, "
        "MIN(value) AS mini, MAX(value) AS maxi "
        f"FROM {_TABLE} "
        f"WHERE {filtre} AND kind = ? AND received_at >= ?"
    )


def _lire(ligne: "dict[str, Any] | None", unit: "str | None") -> IotAggregate:
    if ligne is None:
        return IotAggregate(count=0, unit=unit)
    effectif = int(ligne.get("n") or 0)
    if effectif == 0:
        # AVG rend NULL sur un ensemble vide. Le rendre en zéro ferait passer
        # une absence de mesure pour une mesure nulle.
        return IotAggregate(count=0, unit=unit)
    return IotAggregate(
        count=effectif,
        average=_flottant(ligne.get("moyenne")),
        minimum=_flottant(ligne.get("mini")),
        maximum=_flottant(ligne.get("maxi")),
        unit=unit,
    )


def _flottant(valeur: object) -> "float | None":
    """Nombre rendu par le backend, ramené en flottant.

    PostgreSQL rend `AVG` en `Decimal`, MariaDB en `float`, et SQL Server peut
    rendre un entier quand la colonne l'est. Sans cette conversion, la même
    requête donnerait trois types selon le backend, et une sérialisation JSON
    échouerait sur l'un des trois.
    """
    if valeur is None:
        return None
    try:
        return float(valeur)  # pyright: ignore[reportArgumentType]
    except (TypeError, ValueError):
        return None


def aggregate_for_device(
    site: str,
    device_id: str,
    kind: str,
    *,
    hours: int = 24,
    unit: "str | None" = None,
    db: "_DbAdapter | None" = None,
    now: "datetime | None" = None,
) -> IotAggregate:
    """Moyenne, minimum et maximum d'un équipement sur une fenêtre."""
    debut = window_start(hours, now=now)
    adaptateur = db if db is not None else _default_adapter()
    ligne = adaptateur.fetch_one(
        select_aggregate_sql(by_device=True), (site, device_id, kind, debut)
    )
    return _lire(ligne, unit)


def aggregate_for_site(
    site: str,
    kind: str,
    *,
    hours: int = 24,
    unit: "str | None" = None,
    db: "_DbAdapter | None" = None,
    now: "datetime | None" = None,
) -> IotAggregate:
    """Idem, sur tous les équipements d'un site.

    La moyenne porte sur l'ensemble des mesures, pas sur la moyenne des
    moyennes par équipement : un capteur qui relève dix fois plus souvent pèse
    donc dix fois plus. C'est le comportement d'un `AVG` SQL, et le dire vaut
    mieux que de laisser le supposer.
    """
    debut = window_start(hours, now=now)
    adaptateur = db if db is not None else _default_adapter()
    ligne = adaptateur.fetch_one(
        select_aggregate_sql(by_device=False), (site, kind, debut)
    )
    return _lire(ligne, unit)


def _default_adapter() -> "_DbAdapter":
    from core.database import db

    return db  # pyright: ignore[reportReturnType]
