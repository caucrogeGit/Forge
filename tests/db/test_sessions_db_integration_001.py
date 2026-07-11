"""Intégration réelle du store forge-mvc-sessions-db contre MariaDB (audit tests).

Le store était durci sur retour terrain (SESSIONS-DB-HARDENING-016 : concurrence
optimiste `version`, UTC, purge) mais testé uniquement avec un faux connecteur
capturant le SQL. Ces tests exercent le VRAI store (`DbSessionStore` -> couche
`core.database.db`) contre une MariaDB réelle : roundtrip, garde de `version`,
expiration, purge (`sessions:gc`), flash exactly-once.

Marqués `db` : sautés en local sans base, imposés en CI (`FORGE_REQUIRE_DB=1`).
La table `forge_sessions` est provisionnée depuis le DDL RÉELLEMENT LIVRÉ par le
paquet (la migration embarquée), ce qui vérifie aussi ce DDL sur le moteur.
"""
from __future__ import annotations

import time

import pytest

pytestmark = pytest.mark.db

forge_mvc_sessions_db = pytest.importorskip("forge_mvc_sessions_db")

from forge_mvc_sessions_db.cli.init import iter_sessions_migration_resources
from forge_mvc_sessions_db.store import DbSessionStore


def _ddl_statements() -> list[str]:
    """Statements SQL du DDL forge_sessions livré (commentaires -- retirés)."""
    _, content = next(iter(iter_sessions_migration_resources()))
    raw = content.decode("utf-8")
    sql = "\n".join(l for l in raw.splitlines() if not l.strip().startswith("--"))
    return [s.strip() for s in sql.split(";") if s.strip()]


@pytest.fixture()
def sessions_table(real_db):
    """Crée la table forge_sessions (DDL livré) avant chaque test, la purge après."""
    from core.database import db

    db.execute("DROP TABLE IF EXISTS forge_sessions", ())
    for statement in _ddl_statements():
        db.execute(statement, ())
    yield db
    db.execute("DROP TABLE IF EXISTS forge_sessions", ())


def test_create_get_roundtrip(sessions_table):
    store = DbSessionStore()
    sid = store.create({"panier": [1, 2, 3]})
    loaded = store.get(sid)
    assert loaded is not None
    assert loaded["panier"] == [1, 2, 3]
    assert loaded["authenticated"] is False
    assert loaded["csrf_token"]  # jeton posé à la création


def test_version_starts_zero_and_bumps_on_set(sessions_table):
    db = sessions_table
    store = DbSessionStore()
    sid = store.create()
    row = db.fetch_one("SELECT version FROM forge_sessions WHERE session_id = ?", (sid,))
    assert row["version"] == 0
    store.set(sid, {"x": 1})
    store.set(sid, {"y": 2})
    row = db.fetch_one("SELECT version FROM forge_sessions WHERE session_id = ?", (sid,))
    assert row["version"] == 2, "chaque écriture gardée incrémente version (concurrence optimiste F36)"
    merged = store.get(sid)
    assert merged["x"] == 1 and merged["y"] == 2  # set fusionne


def test_expired_session_not_returned_and_purged(sessions_table):
    db = sessions_table
    store = DbSessionStore()
    live = store.create({"k": "live"})
    dead = store.create({"k": "dead"})
    # Force l'expiration de `dead` dans le passé (le store compare expire_at > now).
    db.execute(
        "UPDATE forge_sessions SET expire_at = '2000-01-01 00:00:00' WHERE session_id = ?",
        (dead,),
    )
    assert store.get(dead) is None, "une session expirée n'est pas renvoyée"
    assert store.get(live) is not None
    purged = store.cleanup_expired()
    assert purged == 1, "cleanup_expired (sessions:gc) purge la ligne expirée"
    assert db.fetch_one("SELECT 1 AS n FROM forge_sessions WHERE session_id = ?", (dead,)) is None
    assert db.fetch_one("SELECT 1 AS n FROM forge_sessions WHERE session_id = ?", (live,)) is not None


def test_flash_read_once(sessions_table):
    store = DbSessionStore()
    sid = store.create()
    assert store.set_flash(sid, "Enregistré", "success") is True
    first = store.get_flash(sid)
    assert first is not None and first["message"] == "Enregistré"
    assert store.get_flash(sid) is None, "le flash est lu une seule fois (exactly-once)"


def test_delete_removes_row(sessions_table):
    db = sessions_table
    store = DbSessionStore()
    sid = store.create()
    store.delete(sid)
    assert store.get(sid) is None
    assert db.fetch_one("SELECT 1 AS n FROM forge_sessions WHERE session_id = ?", (sid,)) is None


def test_short_ttl_expires_naturally(sessions_table):
    """Un TTL nul rend la session immédiatement expirée (horodatage UTC Python, F37)."""
    store = DbSessionStore(ttl=0)
    sid = store.create()
    time.sleep(1.1)
    assert store.get(sid) is None
