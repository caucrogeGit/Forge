# pyright: strict
"""MSSQL-INSERT-IDENTITY-001 — lastrowid lit SCOPE_IDENTITY() dans le lot de l'INSERT.

Dans un lot séparé, ``SCOPE_IDENTITY()`` sort de la portée de l'INSERT et
renvoie toujours NULL : l'adaptateur doit exécuter l'INSERT et la lecture
d'identité dans le même lot, servir l'identité via ``lastrowid`` et le
rowcount de l'INSERT (pas celui du SELECT) via ``rowcount``.

Curseur pyodbc factice : aucun pilote ODBC ni serveur requis (la logique est
aussi prouvée face à un vrai serveur par la suite `db_mssql`).
"""
from __future__ import annotations

from typing import Any

import pytest

pytest.importorskip("forge_mvc_mssql")

from forge_mvc_mssql.backend import _MsCursor  # noqa: E402


class FakePyodbcCursor:
    """Simule le comportement pyodbc face à un lot « INSERT; SELECT SCOPE_IDENTITY() ».

    L'INSERT ne produit qu'un compteur (``description`` None) ; ``nextset()``
    positionne ensuite le curseur sur le résultat du SELECT.
    """

    def __init__(self, identity: "int | None" = 7, insert_rowcount: int = 1) -> None:
        self.executed: "list[tuple[str, tuple[Any, ...]]]" = []
        self.description: "Any" = None
        self.rowcount = -1
        self._identity = identity
        self._insert_rowcount = insert_rowcount
        self._pending_identity = False
        self._row: "Any" = None

    def execute(self, sql: str, params: "Any" = None) -> None:
        self.executed.append((sql, tuple(params) if params else ()))
        if "SELECT SCOPE_IDENTITY()" in sql:
            # Lot INSERT + SELECT : positionné d'abord sur le résultat de
            # l'INSERT (compteur seul), rowcount = lignes insérées.
            self.description = None
            self.rowcount = self._insert_rowcount
            self._pending_identity = True
            self._row = None
        elif sql.lstrip().upper().startswith("SELECT"):
            self.description = (("colonne", None),)
            self.rowcount = -1
            self._row = ("valeur",)
        else:
            self.description = None
            self.rowcount = self._insert_rowcount
            self._row = None

    def nextset(self) -> bool:
        if self._pending_identity:
            self._pending_identity = False
            self.description = (("", None),)
            self.rowcount = -1
            self._row = (self._identity,)
            return True
        return False

    def fetchone(self) -> "Any":
        return self._row


def test_insert_batche_avec_scope_identity_et_lastrowid() -> None:
    fake = FakePyodbcCursor(identity=7, insert_rowcount=1)
    cur = _MsCursor(fake, dictionary=False)
    cur.execute("INSERT INTO contact (nom) VALUES (?)", ("Ada",))

    sql, params = fake.executed[0]
    assert sql == "INSERT INTO contact (nom) VALUES (?); SELECT SCOPE_IDENTITY()"
    assert params == ("Ada",)
    assert cur.lastrowid == 7
    # rowcount = celui de l'INSERT, pas celui du SELECT SCOPE_IDENTITY() (-1).
    assert cur.rowcount == 1


def test_insert_point_virgule_final_normalise() -> None:
    fake = FakePyodbcCursor()
    cur = _MsCursor(fake, dictionary=False)
    cur.execute("INSERT INTO contact (nom) VALUES (?);  ", ("Ada",))

    sql, _ = fake.executed[0]
    assert sql == "INSERT INTO contact (nom) VALUES (?); SELECT SCOPE_IDENTITY()"


def test_identite_null_donne_lastrowid_none() -> None:
    """Table sans colonne identity : SCOPE_IDENTITY() renvoie NULL."""
    fake = FakePyodbcCursor(identity=None)
    cur = _MsCursor(fake, dictionary=False)
    cur.execute("INSERT INTO pivot_sans_identity (a, b) VALUES (?, ?)", (1, 2))

    assert cur.lastrowid is None
    assert cur.rowcount == 1


def test_statement_non_insert_passe_inchange_et_reinitialise() -> None:
    fake = FakePyodbcCursor(identity=7)
    cur = _MsCursor(fake, dictionary=False)
    cur.execute("INSERT INTO contact (nom) VALUES (?)", ("Ada",))
    assert cur.lastrowid == 7

    cur.execute("SELECT nom FROM contact")
    assert fake.executed[-1][0] == "SELECT nom FROM contact"
    # Un statement suivant réinitialise l'identité mémorisée.
    assert cur.lastrowid is None
    assert cur.rowcount == -1


def test_insert_avec_output_non_reecrit() -> None:
    """Un INSERT qui gère déjà son identité (OUTPUT) n'est pas batché."""
    fake = FakePyodbcCursor()
    cur = _MsCursor(fake, dictionary=False)
    sql = "INSERT INTO contact (nom) OUTPUT INSERTED.id VALUES (?)"
    cur.execute(sql, ("Ada",))

    assert fake.executed[0][0] == sql


def test_update_et_delete_non_reecrits() -> None:
    fake = FakePyodbcCursor()
    cur = _MsCursor(fake, dictionary=False)
    cur.execute("UPDATE contact SET nom = ? WHERE id = ?", ("Ada", 1))
    cur.execute("DELETE FROM contact WHERE id = ?", (1,))

    assert fake.executed[0][0] == "UPDATE contact SET nom = ? WHERE id = ?"
    assert fake.executed[1][0] == "DELETE FROM contact WHERE id = ?"
