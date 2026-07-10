"""Garde-fou ADR-054 : le store de session BDD a quitté le cœur.

Le cœur agnostique du SGBD ne fournit plus que MemorySessionStore,
FileSessionStore et le contrat SessionStore. Le store adossé à la BDD vit
dans l'opt-in forge-mvc-sessions-db (DbSessionStore). Ce fichier vérifie
l'absence côté cœur et les invariants de niveau dépôt (fixture SQL, backend
par défaut). Le comportement du store est testé dans le paquet
(packages/forge-mvc-sessions-db/tests/test_db_store_001.py).
"""
from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
_SQL = ROOT / "tests" / "fixtures" / "app" / "mvc" / "models" / "sql" / "forge_sessions.sql"


# ── Extraction : le store BDD n'est plus dans le cœur ─────────────────────────

def test_core_ne_contient_plus_le_store_mariadb():
    assert not (ROOT / "core" / "sessions" / "mariadb_store.py").exists(), (
        "core/sessions/mariadb_store.py doit avoir quitté le cœur (ADR-054, "
        "extrait vers forge-mvc-sessions-db)."
    )


def test_core_sessions_n_exporte_plus_le_store_bdd():
    import core.sessions as sessions

    assert "MariaDbSessionStore" not in sessions.__all__
    assert not hasattr(sessions, "MariaDbSessionStore")
    assert not hasattr(sessions, "DbSessionStore")


def test_store_bdd_vit_dans_l_optin():
    pytest.importorskip("forge_mvc_sessions_db")
    from forge_mvc_sessions_db import DbSessionStore

    assert callable(DbSessionStore)


def test_default_store_is_still_memory_store():
    from core.sessions import MemorySessionStore, get_session_store

    assert isinstance(get_session_store(), MemorySessionStore)


# ── Fixture SQL (table forge_sessions) ────────────────────────────────────────

def test_sql_file_exists():
    assert _SQL.exists()


def test_sql_file_defines_forge_sessions_table():
    sql = _SQL.read_text(encoding="utf-8")
    assert "CREATE TABLE" in sql
    assert "forge_sessions" in sql
    assert "session_id" in sql
    assert "PRIMARY KEY" in sql
    assert "expire_at" in sql


# ── Roadmap (mémoire narrative du ticket d'origine) ───────────────────────────

def test_roadmap_reference_session_mariadb_store_001():
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "SESSION-MARIADB-STORE-001" in content
