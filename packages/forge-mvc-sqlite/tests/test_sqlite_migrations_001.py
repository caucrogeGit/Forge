"""SQLITE-MIGRATIONS-001 — introspection et runner de migrations sur SQLite (ADR-054).

Vérifie que, sous DB_BACKEND=sqlite :
- la connexion des migrations est routée vers le backend (fichier) ;
- l'introspection passe par PRAGMA (load_table_columns) ;
- le runner lit forge_migrations (load_applied_migrations).
"""
from __future__ import annotations

import types
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_sqlite")


def _use_sqlite(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    # ADR-060 : le backend lit le chemin du fichier dans DB_NAME (env).
    monkeypatch.setenv("DB_NAME", str(tmp_path / "app.db"))
    monkeypatch.setattr(
        "cli.project.project_config.load_project_config",
        lambda: types.SimpleNamespace(APP_NAME="t", DB_NAME=str(tmp_path / "app.db")),
    )


def test_introspection_sqlite_via_pragma(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_sqlite(tmp_path, monkeypatch)
    from core.database import backend as backend_module
    from cli.entities import migrations

    backend_module.reset_backend()
    try:
        connection = migrations._connect_db()
        try:
            cursor = connection.cursor()
            cursor.execute(
                "CREATE TABLE contact ("
                "Id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "Nom TEXT NOT NULL, Age INTEGER)"
            )
            connection.commit()
            cols = {c.name: c for c in migrations.load_table_columns("contact", db=connection)}
        finally:
            connection.close()
    finally:
        backend_module.reset_backend()

    assert cols["Id"].auto_increment is True
    assert cols["Nom"].nullable is False
    assert cols["Age"].nullable is True


def test_runner_lit_forge_migrations_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _use_sqlite(tmp_path, monkeypatch)
    from core.database import backend as backend_module
    from cli.entities import migrations

    backend_module.reset_backend()
    try:
        connection = migrations._connect_db()
        try:
            cursor = connection.cursor()
            cursor.execute(backend_module.get_backend().dialect.forge_migrations_ddl())
            cursor.execute(
                migrations.INSERT_APPLIED_MIGRATION_SQL,
                ("20260101000000", "init", "20260101000000_init.sql", "abc123", 5),
            )
            connection.commit()
            applied = migrations.load_applied_migrations(db=connection)
        finally:
            connection.close()
    finally:
        backend_module.reset_backend()

    assert [m.version for m in applied] == ["20260101000000"]
    assert applied[0].filename == "20260101000000_init.sql"
