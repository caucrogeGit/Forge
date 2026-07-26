"""DB-UNIQUE-VIOLATION-CONTRACT-001 (SQL Server) — doublon sur serveur réel.

SQL Server est le cas le plus piégeux : le SQLSTATE `23000` couvre
indifféremment l'unicité, la clé étrangère et le `NOT NULL`. Seul le numéro
natif discrimine (2627 pour une contrainte, 2601 pour un index unique).
Ces garde-fous vérifient que les trois violations restent bien distinguées.

Marqué `db` + `db_mssql` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_MSSQL=1. Noms de tables générés (uuid).
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.errors import UniqueViolationError

pytestmark = [pytest.mark.db, pytest.mark.db_mssql]


def _table() -> str:
    return f"forge_it_uniq_{uuid.uuid4().hex[:12]}"


def test_doublon_leve_unique_violation(real_mssql_db: None) -> None:
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGINT IDENTITY(1,1) PRIMARY KEY, "
        f"email NVARCHAR(100) UNIQUE, nn INT NOT NULL)"
    )
    try:
        db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
        with pytest.raises(UniqueViolationError):
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_not_null_nest_pas_un_doublon(real_mssql_db: None) -> None:
    """Le piège central : NOT NULL partage le SQLSTATE 23000 avec le doublon."""
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGINT IDENTITY(1,1) PRIMARY KEY, "
        f"email NVARCHAR(100) UNIQUE, nn INT NOT NULL)"
    )
    try:
        with pytest.raises(Exception) as info:
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["x@y.z", None])
        assert not isinstance(info.value, UniqueViolationError), (
            "Une violation NOT NULL a ete prise pour un doublon : la detection "
            "s'appuie sur le SQLSTATE 23000 au lieu du numero natif 2627."
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_cle_etrangere_nest_pas_un_doublon(real_mssql_db: None) -> None:
    """Même piège : la clé étrangère renvoie aussi 23000."""
    parent = _table()
    child = _table()
    db.execute(f"CREATE TABLE {parent} (id BIGINT PRIMARY KEY)")
    db.execute(
        f"CREATE TABLE {child} (id BIGINT IDENTITY(1,1) PRIMARY KEY, "
        f"parent_id BIGINT NOT NULL REFERENCES {parent}(id))"
    )
    try:
        with pytest.raises(Exception) as info:
            db.insert(f"INSERT INTO {child} (parent_id) VALUES (?)", [999])
        assert not isinstance(info.value, UniqueViolationError)
    finally:
        db.execute(f"DROP TABLE IF EXISTS {child}")
        db.execute(f"DROP TABLE IF EXISTS {parent}")


def test_erreur_dorigine_chainee(real_mssql_db: None) -> None:
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGINT IDENTITY(1,1) PRIMARY KEY, "
        f"email NVARCHAR(100) UNIQUE)"
    )
    try:
        db.insert(f"INSERT INTO {table} (email) VALUES (?)", ["a@b.c"])
        with pytest.raises(UniqueViolationError) as info:
            db.insert(f"INSERT INTO {table} (email) VALUES (?)", ["a@b.c"])
        assert "2627" in str(info.value.__cause__)
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")
