"""Tests DB-SELECT-COMMIT-001 — commit après SELECT sur connexion possédée.

Sans commit après un SELECT, la connexion retourne au pool avec une transaction
REPEATABLE READ ouverte : l'emprunteur suivant hérite d'un snapshot figé
(lectures périmées). On vérifie via une connexion mockée que `fetch_one` et
`fetch_all` committent quand ils possèdent la connexion (`tx is None`), et qu'une
transaction explicite (`tx=...`) ne committe pas (c'est l'appelant qui gère).
"""

from core.database import db


class _FakeCursor:
    def __init__(self):
        self.lastrowid = 5
        self.rowcount = 1

    def execute(self, *a, **k):
        pass

    def fetchone(self):
        return {"x": 1}

    def fetchall(self):
        return [{"x": 1}]

    def close(self):
        pass


class _FakeConn:
    def __init__(self, calls):
        self._calls = calls

    def cursor(self, dictionary=False):
        return _FakeCursor()

    def commit(self):
        self._calls["commit"] += 1

    def rollback(self):
        self._calls["rollback"] += 1


def _patch(monkeypatch):
    calls = {"commit": 0, "rollback": 0, "closed": 0}
    conn = _FakeConn(calls)
    monkeypatch.setattr(db, "get_connection", lambda: conn)
    monkeypatch.setattr(
        db, "close_connection", lambda c: calls.__setitem__("closed", calls["closed"] + 1)
    )
    return calls, conn


def test_fetch_one_commits_when_owns_connection(monkeypatch):
    calls, _ = _patch(monkeypatch)
    assert db.fetch_one("SELECT 1") == {"x": 1}
    assert calls["commit"] == 1, "fetch_one doit committer la transaction de lecture"
    assert calls["closed"] == 1


def test_fetch_all_commits_when_owns_connection(monkeypatch):
    calls, _ = _patch(monkeypatch)
    assert db.fetch_all("SELECT 1") == [{"x": 1}]
    assert calls["commit"] == 1, "fetch_all doit committer la transaction de lecture"


def test_fetch_does_not_commit_within_explicit_transaction(monkeypatch):
    calls, conn = _patch(monkeypatch)

    class _Tx:
        connection = conn

    db.fetch_all("SELECT 1", tx=_Tx())
    assert calls["commit"] == 0, "une transaction explicite est gérée par l'appelant"
    assert calls["closed"] == 0
