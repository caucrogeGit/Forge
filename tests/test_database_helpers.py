from types import SimpleNamespace

import pytest

from core.database import db
from core.database import transaction as tx_module


class FakeCursor:
    def __init__(self, *, rows=None, one=None, lastrowid=7, rowcount=2, fail=False):
        self.rows = rows or []
        self.one = one
        self.lastrowid = lastrowid
        self.rowcount = rowcount
        self.fail = fail
        self.closed = False
        self.executed = None

    def execute(self, sql, params):
        if self.fail:
            raise RuntimeError("db boom")
        self.executed = (sql, params)

    def fetchone(self):
        return self.one

    def fetchall(self):
        return self.rows

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self, cursor):
        self._cursor = cursor
        self.commits = 0
        self.rollbacks = 0
        self.closed = False
        self.dictionary = None

    def cursor(self, *, dictionary=False):
        self.dictionary = dictionary
        return self._cursor

    def commit(self):
        self.commits += 1

    def rollback(self):
        self.rollbacks += 1

    def close(self):
        self.closed = True


def test_fetch_all_ouvre_et_ferme_hors_transaction(monkeypatch):
    cursor = FakeCursor(rows=[{"Id": 1}])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: connection)
    monkeypatch.setattr(db, "close_connection", lambda conn: conn.close())

    rows = db.fetch_all("SELECT * FROM contact", tx=None)

    assert rows == [{"Id": 1}]
    assert connection.dictionary is True
    assert connection.closed is True
    assert cursor.closed is True


def test_insert_commit_hors_transaction(monkeypatch):
    cursor = FakeCursor(lastrowid=42)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: connection)
    monkeypatch.setattr(db, "close_connection", lambda conn: conn.close())

    result = db.insert("INSERT INTO contact (Nom) VALUES (?)", ("Ada",))

    assert result == 42
    assert connection.commits == 1
    assert connection.rollbacks == 0


def test_execute_reutilise_transaction_sans_commit(monkeypatch):
    cursor = FakeCursor(rowcount=3)
    connection = FakeConnection(cursor)
    tx = SimpleNamespace(connection=connection)

    result = db.execute("DELETE FROM contact_groupe WHERE ContactId = ?", (1,), tx=tx)

    assert result == 3
    assert connection.commits == 0
    assert connection.rollbacks == 0


def test_execute_rollback_hors_transaction_sur_erreur(monkeypatch):
    cursor = FakeCursor(fail=True)
    connection = FakeConnection(cursor)
    monkeypatch.setattr(db, "get_connection", lambda: connection)
    monkeypatch.setattr(db, "close_connection", lambda conn: conn.close())

    with pytest.raises(RuntimeError):
        db.execute("BAD SQL")

    assert connection.rollbacks == 1
    assert connection.closed is True


def test_transaction_commit_et_ferme(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(tx_module, "get_connection", lambda: connection)
    monkeypatch.setattr(tx_module, "close_connection", lambda conn: conn.close())

    with tx_module.transaction() as tx:
        assert tx.connection is connection

    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed is True


def test_transaction_rollback_sur_exception(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(tx_module, "get_connection", lambda: connection)
    monkeypatch.setattr(tx_module, "close_connection", lambda conn: conn.close())

    with pytest.raises(RuntimeError):
        with tx_module.transaction():
            raise RuntimeError("boom")

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed is True
