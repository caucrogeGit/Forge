"""Logique du store de notifications (NOTIFICATIONS-OPTIN-SCAFFOLD-001).

FakeDb en mémoire : on teste notify, la lecture filtrée, le décompte et le
marquage lu sans MariaDB. Le contrat SQL réel est vérifié par le test `db`.
"""
from __future__ import annotations

import json
from typing import Any

import pytest

forge_mvc_notifications = pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications import (
    NotificationError,
    get_notifications,
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)


class FakeDb:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self._next = 1

    def insert(self, sql: str, params: Any = ()) -> int:
        # `target_url` suit la colonne ajoutée par NOTIF-TARGET-URL-001 : le
        # double reste fidèle au schéma réel.
        recipient, type_, message, data, target_url = params
        nid = self._next
        self._next += 1
        self.rows.append({
            "id": nid, "recipient": recipient, "type": type_, "message": message,
            "data": data, "target_url": target_url, "read_at": None,
            "created_at": "2026-06-26 12:00:00",
        })
        return nid

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        recipient, limit = params[0], params[-1]
        rows = [r for r in self.rows if r["recipient"] == recipient]
        if "read_at IS NULL" in sql:
            rows = [r for r in rows if r["read_at"] is None]
        if "id < ?" in sql:
            # Curseur de pagination (NOTIF-PAGINATION-001) : avant-dernier
            # paramètre, la borne de page restant le dernier.
            avant = params[-2]
            rows = [r for r in rows if r["id"] < avant]
        rows = sorted(rows, key=lambda r: r["id"], reverse=True)
        return rows[:limit]

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any] | None:
        if "COUNT(*)" in sql:
            n = sum(1 for r in self.rows if r["recipient"] == params[0] and r["read_at"] is None)
            return {"n": n}
        return None

    def execute(self, sql: str, params: Any = ()) -> int:
        if "WHERE id = ?" in sql:  # mark_read
            for r in self.rows:
                if r["id"] == params[0] and r["read_at"] is None:
                    r["read_at"] = "2026-06-26 12:01:00"
                    return 1
            return 0
        if "WHERE recipient = ?" in sql:  # mark_all_read
            count = 0
            for r in self.rows:
                if r["recipient"] == params[0] and r["read_at"] is None:
                    r["read_at"] = "2026-06-26 12:01:00"
                    count += 1
            return count
        return 0


@pytest.fixture
def db() -> FakeDb:
    return FakeDb()


def test_notify_returns_id_and_serializes_data(db: FakeDb) -> None:
    nid = notify("eleve.42", "Note publiée", type="info", data={"cours": "maths"}, db=db)
    assert nid == 1
    assert json.loads(db.rows[0]["data"]) == {"cours": "maths"}
    assert db.rows[0]["message"] == "Note publiée" and db.rows[0]["read_at"] is None


@pytest.mark.parametrize("recipient,message", [("", "m"), ("r", ""), ("  ", "m"), ("r", "  ")])
def test_notify_empty_raises(db: FakeDb, recipient: str, message: str) -> None:
    with pytest.raises(NotificationError):
        notify(recipient, message, db=db)


def test_notify_non_json_data_raises(db: FakeDb) -> None:
    with pytest.raises(NotificationError):
        notify("r", "m", data={"bad": object()}, db=db)  # type: ignore[dict-item]


def test_get_notifications_most_recent_first(db: FakeDb) -> None:
    notify("r", "1", db=db)
    notify("r", "2", db=db)
    notify("autre", "x", db=db)
    msgs = [n.message for n in get_notifications("r", db=db)]
    assert msgs == ["2", "1"]  # id DESC, autre destinataire exclu


def test_unread_only_and_count(db: FakeDb) -> None:
    notify("r", "1", db=db)
    notify("r", "2", db=db)
    assert unread_count("r", db=db) == 2
    assert mark_read(1, db=db) is True
    assert unread_count("r", db=db) == 1
    assert [n.message for n in get_notifications("r", unread_only=True, db=db)] == ["2"]


def test_mark_read_returns_false_if_already_read(db: FakeDb) -> None:
    notify("r", "1", db=db)
    assert mark_read(1, db=db) is True
    assert mark_read(1, db=db) is False


def test_mark_all_read(db: FakeDb) -> None:
    notify("r", "1", db=db)
    notify("r", "2", db=db)
    notify("autre", "x", db=db)
    assert mark_all_read("r", db=db) == 2
    assert unread_count("r", db=db) == 0
    assert unread_count("autre", db=db) == 1


def test_notification_read_flag_and_data(db: FakeDb) -> None:
    notify("r", "m", data={"k": 1}, db=db)
    n = get_notifications("r", db=db)[0]
    assert n.read is False and n.data == {"k": 1}
    mark_read(1, db=db)
    assert get_notifications("r", db=db)[0].read is True


def test_invalid_limit_raises(db: FakeDb) -> None:
    with pytest.raises(NotificationError):
        get_notifications("r", limit=0, db=db)
