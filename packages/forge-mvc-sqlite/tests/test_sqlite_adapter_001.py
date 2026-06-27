"""SQLITE-ADAPTER-001 — l'adaptateur SQLite respecte les attentes du cœur.

SQLite étant dans la stdlib, on teste l'adaptateur de bout en bout (vrai
fichier base), sans dépendance ni serveur : curseur lignes-dict, `?`, lastrowid,
rowcount, et la couche `core.database.db` câblée sur le backend SQLite.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_sqlite")

import core.forge as forge  # noqa: E402
from forge_mvc_sqlite.backend import SQLiteBackend  # noqa: E402


def _configure(tmp_path: Path) -> None:
    forge.configure(
        app_name="forge_sqlite_test",
        db_host="",
        db_port=0,
        db_user="",
        db_password="",
        db_name=str(tmp_path / "app.db"),
        db_pool_size=1,
    )


def test_adapter_roundtrip_dict_et_lastrowid(tmp_path: Path) -> None:
    _configure(tmp_path)
    backend = SQLiteBackend()
    connection = backend.get_connection()
    try:
        cur = connection.cursor()
        cur.execute(
            "CREATE TABLE contact (id INTEGER PRIMARY KEY AUTOINCREMENT, nom TEXT)"
        )
        cur.execute("INSERT INTO contact (nom) VALUES (?)", ("Ada",))
        assert cur.lastrowid == 1
        connection.commit()

        dict_cur = connection.cursor(dictionary=True)
        dict_cur.execute("SELECT * FROM contact WHERE nom = ?", ("Ada",))
        assert dict_cur.fetchone() == {"id": 1, "nom": "Ada"}

        tuple_cur = connection.cursor()
        tuple_cur.execute("SELECT nom FROM contact")
        assert tuple_cur.fetchone() == ("Ada",)
    finally:
        backend.close_connection(connection)


def test_core_db_facade_sur_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """La façade core.database.db fonctionne en résolvant le backend SQLite."""
    _configure(tmp_path)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    from core.database import backend as backend_module
    from core.database import db

    backend_module.reset_backend()
    try:
        assert backend_module.get_backend().name == "sqlite"
        db.execute(
            "CREATE TABLE item (id INTEGER PRIMARY KEY AUTOINCREMENT, label TEXT)"
        )
        new_id = db.insert("INSERT INTO item (label) VALUES (?)", ("x",))
        assert new_id == 1
        row = db.fetch_one("SELECT * FROM item WHERE id = ?", (1,))
        assert row == {"id": 1, "label": "x"}
        rows = db.fetch_all("SELECT * FROM item")
        assert rows == [{"id": 1, "label": "x"}]
    finally:
        backend_module.reset_backend()
