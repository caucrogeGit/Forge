"""DB-UNIQUE-VIOLATION-CONTRACT-001 (PostgreSQL) — doublon sur serveur réel.

PostgreSQL est le seul backend où le SQLSTATE discrimine vraiment : 23505
pour l'unicité, 23503 pour la clé étrangère, 23502 pour NOT NULL. Ces
garde-fous vérifient que les trois restent bien distingués.

Marqué `db` + `db_pg` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_PG=1. Noms de tables générés (uuid).
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.errors import UniqueViolationError

pytestmark = [pytest.mark.db, pytest.mark.db_pg]


def _table() -> str:
    return f"forge_it_uniq_{uuid.uuid4().hex[:12]}"


def test_doublon_leve_unique_violation(real_pg_db: None) -> None:
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGSERIAL PRIMARY KEY, "
        f"email VARCHAR(100) UNIQUE, nn INTEGER NOT NULL)"
    )
    try:
        db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
        with pytest.raises(UniqueViolationError):
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_not_null_nest_pas_un_doublon(real_pg_db: None) -> None:
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGSERIAL PRIMARY KEY, "
        f"email VARCHAR(100) UNIQUE, nn INTEGER NOT NULL)"
    )
    try:
        with pytest.raises(Exception) as info:
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["x@y.z", None])
        assert not isinstance(info.value, UniqueViolationError)
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_cle_etrangere_nest_pas_un_doublon(real_pg_db: None) -> None:
    parent = _table()
    child = _table()
    db.execute(f"CREATE TABLE {parent} (id BIGINT PRIMARY KEY)")
    db.execute(
        f"CREATE TABLE {child} (id BIGSERIAL PRIMARY KEY, "
        f"parent_id BIGINT NOT NULL REFERENCES {parent}(id))"
    )
    try:
        with pytest.raises(Exception) as info:
            db.insert(f"INSERT INTO {child} (parent_id) VALUES (?)", [999])
        assert not isinstance(info.value, UniqueViolationError)
    finally:
        db.execute(f"DROP TABLE IF EXISTS {child}")
        db.execute(f"DROP TABLE IF EXISTS {parent}")


def test_erreur_dorigine_chainee(real_pg_db: None) -> None:
    table = _table()
    db.execute(f"CREATE TABLE {table} (id BIGSERIAL PRIMARY KEY, email VARCHAR(100) UNIQUE)")
    try:
        db.insert(f"INSERT INTO {table} (email) VALUES (?)", ["a@b.c"])
        with pytest.raises(UniqueViolationError) as info:
            db.insert(f"INSERT INTO {table} (email) VALUES (?)", ["a@b.c"])
        assert getattr(info.value.__cause__, "sqlstate", None) == "23505"
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")
