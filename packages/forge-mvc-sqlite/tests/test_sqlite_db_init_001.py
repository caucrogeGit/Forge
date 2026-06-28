"""SQLITE-DB-INIT-001 — forge db:init fonctionne pour un backend SQLite (ADR-054).

Sous DB_BACKEND=sqlite, init_project_database prend le chemin « sans serveur » :
pas de base ni de comptes à provisionner, juste le fichier et la table
technique forge_migrations. Test de bout en bout sur un vrai fichier SQLite.
"""
from __future__ import annotations

import sqlite3
import types
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_sqlite")


def test_db_init_serverless_cree_forge_migrations(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    from core.database import backend as backend_module
    from cli.entities import db_init

    db_path = tmp_path / "app.db"
    monkeypatch.setattr(
        "cli.project.project_config.load_project_config",
        lambda: types.SimpleNamespace(APP_NAME="demo", DB_NAME=str(db_path)),
    )

    backend_module.reset_backend()
    try:
        actions = db_init.init_project_database()
    finally:
        backend_module.reset_backend()

    assert any("forge_migrations" in a for a in actions), actions
    assert db_path.exists(), "le fichier SQLite doit être créé"

    conn = sqlite3.connect(str(db_path))
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
        }
        assert "forge_migrations" in tables
        # La table est utilisable.
        conn.execute(
            "INSERT INTO forge_migrations (version, name, filename, checksum) "
            "VALUES (?, ?, ?, ?)",
            ("0001", "init", "0001.sql", "deadbeef"),
        )
        conn.commit()
        assert conn.execute("SELECT COUNT(*) FROM forge_migrations").fetchone()[0] == 1
    finally:
        conn.close()
