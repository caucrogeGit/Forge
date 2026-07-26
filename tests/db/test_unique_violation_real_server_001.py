"""DB-UNIQUE-VIOLATION-CONTRACT-001 (MariaDB) — doublon sur serveur réel.

Vérifie contre un vrai MariaDB que `core.database.db` lève
`UniqueViolationError` sur une violation d'unicité, et **seulement** dans ce
cas : une violation `NOT NULL` (errno 1048) partage le même SQLSTATE `23000`
et ne doit pas être confondue avec un doublon (errno 1062).

Marqué `db` : sauté sans serveur, requis en CI via FORGE_REQUIRE_DB=1.
Les noms de tables sont générés (uuid), jamais d'entrée utilisateur dans le DDL.
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.errors import UniqueViolationError

pytestmark = pytest.mark.db


def _table() -> str:
    return f"forge_it_uniq_{uuid.uuid4().hex[:12]}"


def test_doublon_leve_unique_violation(real_db: None) -> None:
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, "
        f"email VARCHAR(100) UNIQUE, nn INT NOT NULL)"
    )
    try:
        db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
        with pytest.raises(UniqueViolationError):
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_not_null_nest_pas_un_doublon(real_db: None) -> None:
    """Le piège : errno 1048 partage le SQLSTATE 23000 avec le doublon."""
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, "
        f"email VARCHAR(100) UNIQUE, nn INT NOT NULL)"
    )
    try:
        with pytest.raises(Exception) as info:
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["x@y.z", None])
        assert not isinstance(info.value, UniqueViolationError), (
            "Une violation NOT NULL (errno 1048) a ete prise pour un doublon : "
            "la detection s'appuie sur le SQLSTATE au lieu de l'errno."
        )
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_erreur_dorigine_chainee(real_db: None) -> None:
    table = _table()
    db.execute(
        f"CREATE TABLE {table} (id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY, "
        f"email VARCHAR(100) UNIQUE, nn INT NOT NULL)"
    )
    try:
        db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
        with pytest.raises(UniqueViolationError) as info:
            db.insert(f"INSERT INTO {table} (email, nn) VALUES (?, ?)", ["a@b.c", 1])
        assert getattr(info.value.__cause__, "errno", None) == 1062
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")
