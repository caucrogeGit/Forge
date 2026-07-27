"""Intégration MariaDB du store de notifications (NOTIFICATIONS-DB-INTEGRATION-001).

Vérifie le contrat SQL réel : `CREATE_TABLE_SQL`, insertion, lecture filtrée,
décompte des non lues, marquage. Marqué `db` : sauté en local, requis en CI.
"""
from __future__ import annotations

import os
import uuid
from typing import Any

import pytest

pytestmark = pytest.mark.db

forge_mvc_notifications = pytest.importorskip("forge_mvc_notifications")

from forge_mvc_notifications import (
    get_notifications,
    mark_all_read,
    mark_read,
    notify,
    unread_count,
)

_REQUIRE_DB = os.environ.get("FORGE_REQUIRE_DB") == "1"


def _rendered_ddl() -> str:
    """DDL de la table, rendu pour le backend actif.

    La constante de schéma du module est supprimée
    (`OPTIN-DDL-CONSTANTS-001`) : deux façons officielles de créer la même
    table contredisaient le principe 11. La source unique est la déclaration
    `forge_mvc_notifications.tables`, rendue par le dialecte.
    """
    from core.database.backend import get_backend
    from core.database.table_ddl import render_create_table
    from forge_mvc_notifications.tables import NOTIFICATIONS

    return chr(10).join(render_create_table(NOTIFICATIONS, get_backend().dialect))

def _params() -> dict[str, Any]:
    return {
        "host": os.environ.get("FORGE_TEST_DB_HOST", "127.0.0.1"),
        "port": int(os.environ.get("FORGE_TEST_DB_PORT", "3306")),
        "user": os.environ.get("FORGE_TEST_DB_USER", "root"),
        "password": os.environ.get("FORGE_TEST_DB_PASSWORD", ""),
    }


class _ConnAdapter:
    def __init__(self, conn: Any, database: str) -> None:
        self._conn = conn
        self._database = database

    def execute(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        rc = cur.rowcount
        cur.close()
        return rc

    def insert(self, sql: str, params: Any = ()) -> int:
        cur = self._conn.cursor()
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        self._conn.commit()
        rid = cur.lastrowid
        cur.close()
        return int(rid)

    def fetch_one(self, sql: str, params: Any = ()) -> dict[str, Any] | None:
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        row = cur.fetchone()
        cur.close()
        return row

    def fetch_all(self, sql: str, params: Any = ()) -> list[dict[str, Any]]:
        cur = self._conn.cursor(dictionary=True)
        cur.execute(f"USE `{self._database}`")
        cur.execute(sql, tuple(params))
        rows = cur.fetchall()
        cur.close()
        return rows


@pytest.fixture
def notif_db() -> Any:
    try:
        import mariadb
    except ImportError:  # pragma: no cover
        pytest.skip("paquet python 'mariadb' non installé")

    params = _params()
    db_name = f"forge_it_notif_{uuid.uuid4().hex[:10]}"
    try:
        admin = mariadb.connect(**params)
    except Exception as error:  # noqa: BLE001
        message = f"MariaDB de test injoignable : {error}"
        if _REQUIRE_DB:
            pytest.fail(message + " (FORGE_REQUIRE_DB=1)")
        pytest.skip(message + " (test d'intégration sauté en local)")

    cur = admin.cursor()
    cur.execute(f"CREATE DATABASE `{db_name}`")
    cur.execute(f"USE `{db_name}`")
    cur.execute(_rendered_ddl())
    admin.commit()
    cur.close()
    try:
        yield _ConnAdapter(admin, db_name)
    finally:
        cur = admin.cursor()
        cur.execute(f"DROP DATABASE IF EXISTS `{db_name}`")
        admin.commit()
        cur.close()
        admin.close()


def test_notify_then_read_most_recent_first(notif_db: _ConnAdapter) -> None:
    notify("eleve.42", "Première", data={"k": 1}, db=notif_db)
    notify("eleve.42", "Seconde", db=notif_db)
    notify("autre", "x", db=notif_db)
    entries = get_notifications("eleve.42", db=notif_db)
    assert [n.message for n in entries] == ["Seconde", "Première"]
    assert entries[1].data == {"k": 1}


def test_unread_count_and_mark_read(notif_db: _ConnAdapter) -> None:
    nid = notify("eleve.42", "m", db=notif_db)
    notify("eleve.42", "m2", db=notif_db)
    assert unread_count("eleve.42", db=notif_db) == 2
    assert mark_read(nid, db=notif_db) is True
    assert mark_read(nid, db=notif_db) is False  # déjà lue
    assert unread_count("eleve.42", db=notif_db) == 1


def test_unread_only_filter(notif_db: _ConnAdapter) -> None:
    a = notify("r", "lu", db=notif_db)
    notify("r", "non lu", db=notif_db)
    mark_read(a, db=notif_db)
    msgs = [n.message for n in get_notifications("r", unread_only=True, db=notif_db)]
    assert msgs == ["non lu"]


def test_mark_all_read(notif_db: _ConnAdapter) -> None:
    notify("r", "1", db=notif_db)
    notify("r", "2", db=notif_db)
    assert mark_all_read("r", db=notif_db) == 2
    assert unread_count("r", db=notif_db) == 0
