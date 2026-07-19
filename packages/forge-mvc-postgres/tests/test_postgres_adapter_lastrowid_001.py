# pyright: strict
"""PG-INSERT-IDENTITY-001 — lastrowid protège lastval() par un savepoint.

Sans garde, ``SELECT lastval()`` lève une erreur si aucune séquence n'a été
touchée dans la session ; en bloc de transaction, cette erreur avorte la
transaction et l'INSERT serait perdu au commit. L'adaptateur doit lire
lastval() sous savepoint, restaurer le savepoint en cas d'échec (transaction
préservée) et renvoyer None plutôt que de lever.

Curseur psycopg factice : ni psycopg ni serveur requis (statut Alpha, logique
testée unitairement).
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_postgres")

from forge_mvc_postgres.backend import _PgCursor  # noqa: E402


class FakePsycopgCursor:
    """Simule un curseur psycopg : lastval() et savepoints configurables."""

    def __init__(
        self,
        lastval: "int | None" = 42,
        fail_lastval: bool = False,
        fail_savepoint: bool = False,
    ) -> None:
        self.executed: "list[str]" = []
        self._lastval = lastval
        self._fail_lastval = fail_lastval
        self._fail_savepoint = fail_savepoint
        self._row: "Any" = None

    def execute(self, sql: str, params: "Any" = None) -> None:
        self.executed.append(sql)
        if sql == "SAVEPOINT forge_lastrowid" and self._fail_savepoint:
            raise RuntimeError("SAVEPOINT can only be used in transaction blocks")
        if sql == "SELECT lastval()":
            if self._fail_lastval:
                raise RuntimeError("lastval is not yet defined in this session")
            self._row = (self._lastval,)

    def fetchone(self) -> "Any":
        return self._row


def test_lastrowid_nominal_sous_savepoint() -> None:
    fake = FakePsycopgCursor(lastval=42)
    cur = _PgCursor(fake)

    assert cur.lastrowid == 42
    assert fake.executed == [
        "SAVEPOINT forge_lastrowid",
        "SELECT lastval()",
        "RELEASE SAVEPOINT forge_lastrowid",
    ]


def test_lastval_indefini_restaure_le_savepoint() -> None:
    """Aucune séquence touchée : None, et la transaction est préservée."""
    fake = FakePsycopgCursor(fail_lastval=True)
    cur = _PgCursor(fake)

    assert cur.lastrowid is None
    assert fake.executed == [
        "SAVEPOINT forge_lastrowid",
        "SELECT lastval()",
        "ROLLBACK TO SAVEPOINT forge_lastrowid",
    ]


def test_autocommit_sans_savepoint_lit_directement() -> None:
    """Hors bloc de transaction, la garde est inutile : lecture directe."""
    fake = FakePsycopgCursor(lastval=7, fail_savepoint=True)
    cur = _PgCursor(fake)

    assert cur.lastrowid == 7
    assert fake.executed == [
        "SAVEPOINT forge_lastrowid",
        "SELECT lastval()",
    ]


def test_autocommit_et_lastval_indefini_donne_none() -> None:
    fake = FakePsycopgCursor(fail_lastval=True, fail_savepoint=True)
    cur = _PgCursor(fake)

    assert cur.lastrowid is None


def test_lastrowid_convertit_en_int() -> None:
    fake = FakePsycopgCursor(lastval=13)
    cur = _PgCursor(fake)

    value = cur.lastrowid
    assert value == 13
    assert isinstance(value, int)
