"""TEST-DB-INTEGRATION-CI-001 — intégration de la couche DB sur une vraie MariaDB.

Exerce la VRAIE couche `core.database.db` (fetch_one/fetch_all/execute/insert) et
les transactions explicites contre un serveur MariaDB réel, là où le reste de la
suite mocke la base. Valide en particulier, face au moteur :
- l'aller-retour insert/fetch et le rowcount des UPDATE/DELETE ;
- que les requêtes paramétrées LIENT les valeurs (pas d'interpolation) ;
- le commit et le rollback d'une transaction explicite ;
- l'application réelle d'une contrainte de clé étrangère.

Marqué `db` : sauté en local sans base, requis en CI (voir tests/db/conftest.py).
Les noms de tables sont générés (uuid), jamais d'entrée utilisateur dans le DDL.
"""
from __future__ import annotations

import uuid

import pytest

from core.database import db
from core.database.transaction import transaction

pytestmark = pytest.mark.db


def _table(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def test_insert_fetch_roundtrip(real_db: None) -> None:
    table = _table("forge_it_users")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100) NOT NULL)")
    try:
        new_id = db.insert(f"INSERT INTO {table} (name) VALUES (?)", ["Alice"])
        assert isinstance(new_id, int) and new_id > 0
        row = db.fetch_one(f"SELECT id, name FROM {table} WHERE id = ?", [new_id])
        assert row == {"id": new_id, "name": "Alice"}
        db.insert(f"INSERT INTO {table} (name) VALUES (?)", ["Bob"])
        rows = db.fetch_all(f"SELECT name FROM {table} ORDER BY id")
        assert [r["name"] for r in rows] == ["Alice", "Bob"]
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_execute_update_and_delete_return_rowcount(real_db: None) -> None:
    table = _table("forge_it_items")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY, label VARCHAR(50))")
    try:
        db.insert(f"INSERT INTO {table} (id, label) VALUES (?, ?)", [1, "a"])
        db.insert(f"INSERT INTO {table} (id, label) VALUES (?, ?)", [2, "b"])
        updated = db.execute(f"UPDATE {table} SET label = ? WHERE id = ?", ["A", 1])
        assert updated == 1
        deleted = db.execute(f"DELETE FROM {table} WHERE id = ?", [2])
        assert deleted == 1
        remaining = db.fetch_all(f"SELECT label FROM {table}")
        assert [r["label"] for r in remaining] == ["A"]
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_parameters_bind_and_block_injection(real_db: None) -> None:
    # La promesse « SQL sûr » vérifiée contre le vrai moteur : une charge
    # d'injection est traitée comme une donnée littérale, jamais comme du SQL.
    table = _table("forge_it_inj")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY AUTO_INCREMENT, name VARCHAR(100))")
    try:
        payload = "Robert'); DROP TABLE students;--"
        db.insert(f"INSERT INTO {table} (name) VALUES (?)", [payload])
        # La table existe toujours et la valeur est stockée telle quelle.
        row = db.fetch_one(f"SELECT name FROM {table} WHERE name = ?", [payload])
        assert row is not None and row["name"] == payload
        # Une valeur « OR 1=1 » liée ne renvoie rien (pas interprétée comme du SQL).
        bogus = db.fetch_all(f"SELECT id FROM {table} WHERE name = ?", ["x' OR '1'='1"])
        assert bogus == []
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_transaction_commit_persists(real_db: None) -> None:
    table = _table("forge_it_tx")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY)")
    try:
        with transaction() as tx:
            db.insert(f"INSERT INTO {table} (id) VALUES (?)", [1], tx=tx)
            db.insert(f"INSERT INTO {table} (id) VALUES (?)", [2], tx=tx)
        rows = db.fetch_all(f"SELECT id FROM {table} ORDER BY id")
        assert [r["id"] for r in rows] == [1, 2]
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_transaction_rollback_discards(real_db: None) -> None:
    table = _table("forge_it_rb")
    db.execute(f"CREATE TABLE {table} (id INT PRIMARY KEY)")
    try:
        with pytest.raises(RuntimeError):
            with transaction() as tx:
                db.insert(f"INSERT INTO {table} (id) VALUES (?)", [1], tx=tx)
                raise RuntimeError("boom")  # déclenche le rollback du gestionnaire
        rows = db.fetch_all(f"SELECT id FROM {table}")
        assert rows == []  # rien n'a été persisté
    finally:
        db.execute(f"DROP TABLE IF EXISTS {table}")


def test_foreign_key_constraint_is_enforced(real_db: None) -> None:
    import mariadb

    parent = _table("forge_it_parent")
    child = _table("forge_it_child")
    db.execute(f"CREATE TABLE {parent} (id INT PRIMARY KEY) ENGINE=InnoDB")
    db.execute(
        f"CREATE TABLE {child} (id INT PRIMARY KEY, parent_id INT, "
        f"FOREIGN KEY (parent_id) REFERENCES {parent}(id)) ENGINE=InnoDB"
    )
    try:
        db.insert(f"INSERT INTO {parent} (id) VALUES (?)", [1])
        db.insert(f"INSERT INTO {child} (id, parent_id) VALUES (?, ?)", [10, 1])
        # parent_id inexistant : la contrainte FK rejette réellement l'insertion.
        with pytest.raises(mariadb.Error):
            db.insert(f"INSERT INTO {child} (id, parent_id) VALUES (?, ?)", [11, 999])
    finally:
        db.execute(f"DROP TABLE IF EXISTS {child}")
        db.execute(f"DROP TABLE IF EXISTS {parent}")
