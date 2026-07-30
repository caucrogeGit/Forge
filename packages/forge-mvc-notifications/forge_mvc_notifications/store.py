# pyright: strict
"""Notifications applicatives in-app, persistées dans MariaDB.

`forge-mvc-notifications` stocke des notifications destinées aux utilisateurs de
l'application (élève inscrit, note publiée, devoir à rendre) dans une table
`notifications`. L'API est explicite : on crée avec :func:`notify`, on lit avec
:func:`get_notifications`, on marque lu avec :func:`mark_read`. Le SQL reste
visible.

Périmètre V1 : notifications **in-app** (des lignes en base, lues dans l'IHM).
La livraison hors application (email, push) est à la charge de l'application, par
exemple en combinant ce paquet avec `forge-mvc-jobs` et `forge-mvc-mail`. La
dépendance va de l'opt-in vers le cœur, jamais l'inverse.

La table n'est PAS créée automatiquement : voir `forge notifications:init` puis
`forge migration:apply`.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from forge_mvc_notifications.errors import NotificationError

#: Nom de la table de notifications.
TABLE_NAME = "notifications"

#: Plafond strict du nombre de notifications lues d'un coup.
MAX_LIMIT = 1000


_INSERT_SQL = (
    f"INSERT INTO {TABLE_NAME} (recipient, type, message, data) VALUES (?, ?, ?, ?)"
)
_SELECT_COLUMNS = "id, recipient, type, message, data, read_at, created_at"
_UNREAD_COUNT_SQL = (
    f"SELECT COUNT(*) AS n FROM {TABLE_NAME} WHERE recipient = ? AND read_at IS NULL"
)


def _now() -> str:
    """Expression de l'instant courant, propre au backend (OPTIN-DML-DIALECT-001).

    `NOW()` était écrit en dur : mesuré, SQL Server et SQLite ne le connaissent
    pas, et marquer une notification comme lue y échouait malgré une DDL déjà
    dialectale.
    """
    from core.database.backend import get_backend

    return get_backend().dialect.now_expression()


def _mark_read_sql() -> str:
    return f"UPDATE {TABLE_NAME} SET read_at = {_now()} WHERE id = ? AND read_at IS NULL"


def _mark_all_read_sql() -> str:
    return (f"UPDATE {TABLE_NAME} SET read_at = {_now()} "
            "WHERE recipient = ? AND read_at IS NULL")


@dataclass(frozen=True)
class Notification:
    """Une notification lue depuis la table."""

    id: int
    recipient: str
    type: str
    message: str
    data: dict[str, Any]
    read: bool
    created_at: str


def _db_module() -> Any:
    import core.database.db as db  # noqa: PLC0415

    return db


def notify(
    recipient: str,
    message: str,
    *,
    type: str = "info",
    data: dict[str, Any] | None = None,
    db: Any = None,
) -> int:
    """Crée une notification pour `recipient` et renvoie son identifiant.

    `recipient` et `message` sont obligatoires. `type` qualifie la notification
    (par exemple ``"info"``, ``"alerte"``). `data` est un complément libre
    sérialisé en JSON. Lève :class:`NotificationError` si `recipient`/`message`
    est vide ou si `data` n'est pas sérialisable en JSON.
    """
    if not recipient or not recipient.strip():
        raise NotificationError("Le destinataire ne peut pas être vide.")
    if not message or not message.strip():
        raise NotificationError("Le message ne peut pas être vide.")
    try:
        data_json = json.dumps(data or {})
    except (TypeError, ValueError) as exc:
        raise NotificationError(f"Données non sérialisables en JSON : {exc}") from exc
    return (db if db is not None else _db_module()).insert(
        _INSERT_SQL, (recipient, type, message, data_json)
    )


def get_notifications(
    recipient: str,
    *,
    unread_only: bool = False,
    limit: int = 50,
    db: Any = None,
) -> list[Notification]:
    """Renvoie les notifications de `recipient`, les plus récentes d'abord.

    `unread_only` ne renvoie que les non lues. `limit` est borné à
    :data:`MAX_LIMIT`. Lève :class:`NotificationError` si `limit` est négatif ou
    nul.
    """
    if limit < 1:
        raise NotificationError(f"limit doit être >= 1. Reçu : {limit}.")
    limit = min(limit, MAX_LIMIT)
    where = "WHERE recipient = ?"
    params: list[object] = [recipient]
    if unread_only:
        where += " AND read_at IS NULL"
    from core.database.backend import get_backend

    # La borne appartient au dialecte : T-SQL ne connaît pas LIMIT.
    sql = (
        f"SELECT {_SELECT_COLUMNS} FROM {TABLE_NAME} {where} ORDER BY id DESC"
        f"{get_backend().dialect.limit_clause()}"
    )
    params.append(limit)
    rows = (db if db is not None else _db_module()).fetch_all(sql, params)
    return [
        Notification(
            id=int(row["id"]),
            recipient=str(row["recipient"]),
            type=str(row["type"]),
            message=str(row["message"]),
            data=json.loads(row["data"]),
            read=row["read_at"] is not None,
            created_at=str(row["created_at"]),
        )
        for row in rows
    ]


def unread_count(recipient: str, *, db: Any = None) -> int:
    """Nombre de notifications non lues de `recipient`."""
    row = (db if db is not None else _db_module()).fetch_one(_UNREAD_COUNT_SQL, (recipient,))
    return int(row["n"]) if row else 0


def mark_read(notification_id: int, *, db: Any = None) -> bool:
    """Marque une notification comme lue. Renvoie `True` si elle était non lue."""
    return (db if db is not None else _db_module()).execute(_mark_read_sql(), (notification_id,)) > 0


def mark_all_read(recipient: str, *, db: Any = None) -> int:
    """Marque toutes les notifications de `recipient` comme lues. Renvoie le nombre marqué."""
    return (db if db is not None else _db_module()).execute(_mark_all_read_sql(), (recipient,))
