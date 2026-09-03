# pyright: strict
"""Compteur de sessions actives (`SESSIONS-ACTIVE-METRIC-001`).

`sessions:gc` dit combien de sessions il a purgées. Personne ne pouvait dire
combien il en reste, ni comment ce nombre évolue.

C'est pourtant la première chose qu'on veut savoir d'un magasin de sessions
adossé à la base : une table qui grossit sans fin signale une purge qui ne
tourne pas, et une chute brutale signale une déconnexion de masse.

## Ce que « active » veut dire ici

Une session non expirée à l'instant de la lecture. Le filtre est posé **en
SQL** : compter toutes les lignes puis écarter les expirées en Python
rapatrierait une table entière pour en rendre un nombre.

Une session expirée que la purge n'a pas encore retirée n'est **pas** active :
elle occupe la table sans plus servir à personne, et la compter ferait passer
un retard de purge pour de la fréquentation.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Protocol

from forge_mvc_sessions_db.tables import FORGE_SESSIONS
from forge_mvc_sessions_db.ttl import SESSION_KINDS

__all__ = [
    "SessionMetrics",
    "COUNT_ACTIVE_SQL",
    "COUNT_BY_KIND_SQL",
    "COUNT_EXPIRED_SQL",
    "active_sessions",
    "session_metrics",
]

_TABLE = FORGE_SESSIONS.name

#: Le SQL reste visible (principe 5).
COUNT_ACTIVE_SQL = f"SELECT COUNT(*) AS total FROM {_TABLE} WHERE expire_at > ?"
COUNT_EXPIRED_SQL = f"SELECT COUNT(*) AS total FROM {_TABLE} WHERE expire_at <= ?"
COUNT_BY_KIND_SQL = (
    f"SELECT kind, COUNT(*) AS total FROM {_TABLE} "
    "WHERE expire_at > ? GROUP BY kind"
)


class _Db(Protocol):
    def fetch_one(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "dict[str, Any] | None": ...

    def fetch_all(
        self, sql: str, params: "tuple[Any, ...]"
    ) -> "list[dict[str, Any]]": ...


@dataclass(frozen=True)
class SessionMetrics:
    """Photographie du magasin à un instant."""

    active: int
    expired: int
    by_kind: "dict[str, int]"

    @property
    def total(self) -> int:
        """Lignes présentes dans la table, actives ou non.

        C'est ce nombre là qui dit si la purge suit : une table qui grossit
        pendant que `active` stagne signale une purge qui ne tourne pas.
        """
        return self.active + self.expired

    @property
    def purge_backlog_ratio(self) -> float:
        """Part des lignes qui ne servent plus. Zéro quand la table est vide.

        Au delà de la moitié, la purge est en retard : la table coûte deux fois
        ce qu'elle devrait à chaque balayage.
        """
        return 0.0 if self.total == 0 else self.expired / self.total

    def as_dict(self) -> "dict[str, Any]":
        return {
            "active": self.active,
            "expired": self.expired,
            "total": self.total,
            "by_kind": dict(self.by_kind),
        }


def _maintenant(now: "datetime | None") -> datetime:
    return now or datetime.now(UTC).replace(tzinfo=None)


def active_sessions(
    *, db: "_Db | None" = None, now: "datetime | None" = None
) -> int:
    """Nombre de sessions non expirées.

    Le filtre est en SQL : compter toutes les lignes puis écarter les expirées
    en Python rapatrierait une table entière pour en rendre un nombre.
    """
    acces = db if db is not None else _defaut()
    ligne = acces.fetch_one(COUNT_ACTIVE_SQL, (_maintenant(now),))
    return int(ligne.get("total") or 0) if ligne else 0


def session_metrics(
    *, db: "_Db | None" = None, now: "datetime | None" = None
) -> SessionMetrics:
    """Actives, expirées, et réparties par nature.

    Les trois natures figurent **toujours** dans `by_kind`, à zéro le cas
    échéant : une clé absente et une valeur nulle se lisent différemment dans
    un tableau de bord, et l'absence ferait croire à une métrique cassée.
    """
    acces = db if db is not None else _defaut()
    instant = _maintenant(now)

    actives = acces.fetch_one(COUNT_ACTIVE_SQL, (instant,))
    expirees = acces.fetch_one(COUNT_EXPIRED_SQL, (instant,))

    par_nature = {nature: 0 for nature in sorted(SESSION_KINDS)}
    for ligne in acces.fetch_all(COUNT_BY_KIND_SQL, (instant,)):
        nature = str(ligne.get("kind") or "")
        if nature in par_nature:
            par_nature[nature] = int(ligne.get("total") or 0)

    return SessionMetrics(
        active=int(actives.get("total") or 0) if actives else 0,
        expired=int(expirees.get("total") or 0) if expirees else 0,
        by_kind=par_nature,
    )


def _defaut() -> "_Db":
    from core.database import db

    return db  # pyright: ignore[reportReturnType]
