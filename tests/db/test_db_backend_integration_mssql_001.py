"""CI-DB-MSSQL-001 (ADR-084) — intégration de la couche DB sur un vrai SQL Server.

Exerce la VRAIE couche `core.database.db` contre un serveur SQL Server réel,
miroir de test_db_integration_001 (MariaDB) : aller-retour insert/fetch avec
identité d'insertion (SCOPE_IDENTITY() dans le lot de l'INSERT,
MSSQL-INSERT-IDENTITY-001), rowcount des UPDATE/DELETE, liaison des paramètres
(anti-injection), commit et rollback d'une transaction explicite, contrainte de
clé étrangère.

Marqué `db` + `db_mssql` : sauté sans serveur, requis en CI via
FORGE_REQUIRE_DB_MSSQL=1. Les noms de tables sont générés (uuid), jamais
d'entrée utilisateur dans le DDL.
"""
from __future__ import annotations

import uuid

import pytest

from core.database.errors import ForeignKeyViolationError

from core.database import db
from core.database.transaction import transaction

pytestmark = [pytest.mark.db, pytest.mark.db_mssql]


def _table(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def test_insert_fetch_roundtrip_et_lastrowid(real_mssql_db: None) -> None:
    table = _table("forge_it_ms_users")
    db.execute(
        f"CREATE TABLE {table} (id BIGINT IDENTITY(1,1) PRIMARY KEY, "
        f"name NVARCHAR(100) NOT NULL)"
    )
    try:
        # MSSQL-INSERT-IDENTITY-001 : db.insert retourne l'identité réelle
        # (SCOPE_IDENTITY() dans le lot de l'INSERT), prouvé face au moteur.
        new_id = db.insert(f"INSERT INTO {table} (name) VALUES (?)", ["Alice"])
        assert isinstance(new_id, int) and new_id > 0
        row = db.fetch_one(f"SELECT id, name FROM {table} WHERE id = ?", [new_id])
        assert row == {"id": new_id, "name": "Alice"}
        second_id = db.insert(f"INSERT INTO {table} (name) VALUES (?)", ["Bob"])
        assert second_id == new_id + 1
        rows = db.fetch_all(f"SELECT name FROM {table} ORDER BY id")
        assert [r["name"] for r in rows] == ["Alice", "Bob"]
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_execute_update_and_delete_return_rowcount(real_mssql_db: None) -> None:
    table = _table("forge_it_ms_items")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY, label NVARCHAR(50))")
    try:
        db.execute(f"INSERT INTO {table} (id, label) VALUES (?, ?)", [1, "a"])
        db.execute(f"INSERT INTO {table} (id, label) VALUES (?, ?)", [2, "b"])
        updated = db.execute(f"UPDATE {table} SET label = ? WHERE id = ?", ["A", 1])
        assert updated == 1
        deleted = db.execute(f"DELETE FROM {table} WHERE id = ?", [2])
        assert deleted == 1
        remaining = db.fetch_all(f"SELECT label FROM {table}")
        assert [r["label"] for r in remaining] == ["A"]
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_parameters_bind_and_block_injection(real_mssql_db: None) -> None:
    # La promesse « SQL sûr » vérifiée contre le vrai moteur : une charge
    # d'injection est traitée comme une donnée littérale, jamais comme du SQL.
    table = _table("forge_it_ms_inj")
    db.execute(
        f"CREATE TABLE {table} (id BIGINT IDENTITY(1,1) PRIMARY KEY, name NVARCHAR(100))"
    )
    try:
        payload = "Robert'); DROP TABLE students;--"
        db.insert(f"INSERT INTO {table} (name) VALUES (?)", [payload])
        row = db.fetch_one(f"SELECT name FROM {table} WHERE name = ?", [payload])
        assert row is not None and row["name"] == payload
        bogus = db.fetch_all(f"SELECT id FROM {table} WHERE name = ?", ["x' OR '1'='1"])
        assert bogus == []
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_lastrowid_sans_identity_donne_none(real_mssql_db: None) -> None:
    # Table sans colonne identity : SCOPE_IDENTITY() renvoie NULL, db.insert
    # retourne None et l'insertion est bien acquise (MSSQL-INSERT-IDENTITY-001).
    table = _table("forge_it_ms_noid")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY, label NVARCHAR(50))")
    try:
        result = db.insert(f"INSERT INTO {table} (id, label) VALUES (?, ?)", [1, "x"])
        assert result is None
        row = db.fetch_one(f"SELECT id, label FROM {table} WHERE id = ?", [1])
        assert row == {"id": 1, "label": "x"}
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_transaction_commit_persists(real_mssql_db: None) -> None:
    table = _table("forge_it_ms_tx")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY)")
    try:
        with transaction() as tx:
            db.execute(f"INSERT INTO {table} (id) VALUES (?)", [1], tx=tx)
            db.execute(f"INSERT INTO {table} (id) VALUES (?)", [2], tx=tx)
        rows = db.fetch_all(f"SELECT id FROM {table} ORDER BY id")
        assert [r["id"] for r in rows] == [1, 2]
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_transaction_rollback_discards(real_mssql_db: None) -> None:
    table = _table("forge_it_ms_rb")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY)")
    try:
        with pytest.raises(RuntimeError):
            with transaction() as tx:
                db.execute(f"INSERT INTO {table} (id) VALUES (?)", [1], tx=tx)
                raise RuntimeError("boom")  # déclenche le rollback du gestionnaire
        rows = db.fetch_all(f"SELECT id FROM {table}")
        assert rows == []  # rien n'a été persisté
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_foreign_key_constraint_is_enforced(real_mssql_db: None) -> None:

    parent = _table("forge_it_ms_parent")
    child = _table("forge_it_ms_child")
    db.execute(f"CREATE TABLE {parent} (id INT PRIMARY KEY)")
    db.execute(
        f"CREATE TABLE {child} (id INT PRIMARY KEY, parent_id INT "
        f"REFERENCES {parent}(id))"
    )
    try:
        db.execute(f"INSERT INTO {parent} (id) VALUES (?)", [1])
        db.execute(f"INSERT INTO {child} (id, parent_id) VALUES (?, ?)", [10, 1])
        # parent_id inexistant : la contrainte FK rejette réellement l'insertion.
        # DB-ERROR-MESSAGES-HOMOGENES-001 : la violation est désormais
        # QUALIFIÉE. Le test attendait l'exception brute du pilote, ce que
        # l'ADR-054 refuse précisément : une application qui l'attrape n'est
        # portable sur aucun autre backend.
        with pytest.raises(ForeignKeyViolationError):
            db.execute(f"INSERT INTO {child} (id, parent_id) VALUES (?, ?)", [11, 999])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {child}")
        db.execute(f"DROP TABLE IF EXISTS {parent}")
