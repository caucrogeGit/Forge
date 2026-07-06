"""MARIADB-ADMIN-CONNECTION-001 — get_admin_connection (ADR-054, ADR-060).

Vérifie que la connexion d'administration passe par mariadb.connect avec les
identifiants lus dans l'environnement (DB_ADMIN_*, ADR-060), `database` omis
quand absent (db:init) et présent sinon (db:apply / migrations).
"""
from __future__ import annotations

import sys
import types

import pytest

pytest.importorskip("forge_mvc_mariadb")
from forge_mvc_mariadb.backend import MariaDBBackend  # noqa: E402


def _fake_mariadb(captured: dict[str, object]) -> types.ModuleType:
    module = types.ModuleType("mariadb")

    def connect(**kwargs: object) -> str:
        captured.update(kwargs)
        return "fake-admin-connection"

    module.connect = connect  # type: ignore[attr-defined]
    return module


def _set_admin_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DB_HOST", "db.local")
    monkeypatch.setenv("DB_PORT", "3306")
    monkeypatch.setenv("DB_ADMIN_LOGIN", "root")
    monkeypatch.setenv("DB_ADMIN_PWD", "s3cret")


def test_admin_connection_sans_database(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setitem(sys.modules, "mariadb", _fake_mariadb(captured))
    _set_admin_env(monkeypatch)
    conn = MariaDBBackend().get_admin_connection()
    assert conn == "fake-admin-connection"
    assert captured == {
        "host": "db.local",
        "port": 3306,
        "user": "root",
        "password": "s3cret",
    }
    assert "database" not in captured


def test_admin_connection_avec_database(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, object] = {}
    monkeypatch.setitem(sys.modules, "mariadb", _fake_mariadb(captured))
    _set_admin_env(monkeypatch)
    MariaDBBackend().get_admin_connection(database="app")
    assert captured["database"] == "app"
    assert captured["user"] == "root"
