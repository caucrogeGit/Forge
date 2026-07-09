"""OPTIN-REGISTRY-BACKEND-001 (ADR-061) — db:init inscrit le backend au registre.

Le backend BDD choisi (résolu par entry point, ADR-054/060) est enregistré dans
`BACKEND` du registre par `forge db:init`. Best-effort : silencieux si le registre
est absent.
"""
from __future__ import annotations

import sqlite3
import types

import pytest

from cli.optins.registry_format import (
    REGISTRY_TEMPLATE,
    read_backend,
    set_backend,
)


# ── set_backend (source unique) ──────────────────────────────────────────────

def test_set_backend_fixe_la_valeur():
    text = set_backend(REGISTRY_TEMPLATE, "sqlite")
    assert read_backend(text) == "sqlite"


def test_set_backend_none_remet_a_none():
    text = set_backend(REGISTRY_TEMPLATE, "mariadb")
    text = set_backend(text, None)
    assert read_backend(text) is None


def test_set_backend_sans_affectation_inchange():
    assert set_backend("x = 1\n", "sqlite") == "x = 1\n"


# ── Intégration : db:init (SQLite) inscrit le backend ────────────────────────

def test_db_init_inscrit_backend_dans_registry(tmp_path, monkeypatch):
    pytest.importorskip("forge_mvc_sqlite")
    from core.database import backend as backend_module
    from forge_mvc_entities import db_init

    (tmp_path / "optins").mkdir()
    (tmp_path / "optins" / "registry.py").write_text(REGISTRY_TEMPLATE, encoding="utf-8")

    db_path = tmp_path / "app.db"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("DB_NAME", str(db_path))
    monkeypatch.setattr(
        "cli.project.project_config.load_project_config",
        lambda: types.SimpleNamespace(APP_NAME="demo", DB_NAME=str(db_path)),
    )

    backend_module.reset_backend()
    try:
        db_init.init_project_database()
    finally:
        backend_module.reset_backend()

    reg = (tmp_path / "optins" / "registry.py").read_text(encoding="utf-8")
    assert read_backend(reg) == "sqlite"
    assert db_path.exists()  # sanity : l'init serverless a bien tourné
    sqlite3.connect(str(db_path)).close()


def test_db_init_sans_registre_ne_plante_pas(tmp_path, monkeypatch):
    pytest.importorskip("forge_mvc_sqlite")
    from core.database import backend as backend_module
    from forge_mvc_entities import db_init

    db_path = tmp_path / "app.db"
    monkeypatch.chdir(tmp_path)  # pas de optins/registry.py
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    monkeypatch.setenv("DB_NAME", str(db_path))
    monkeypatch.setattr(
        "cli.project.project_config.load_project_config",
        lambda: types.SimpleNamespace(APP_NAME="demo", DB_NAME=str(db_path)),
    )

    backend_module.reset_backend()
    try:
        actions = db_init.init_project_database()
    finally:
        backend_module.reset_backend()

    assert any("forge_migrations" in a for a in actions)  # a fonctionné sans registre
