"""Tests pour SESSION-MARIADB-STORE-001 — Backend session MariaDB.

Aucune connexion MariaDB réelle n'est requise : _FakeDB simule les
opérations SQL en mémoire via les callables injectables du store.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ── Fausse base de données ────────────────────────────────────────────────────


class _FakeDB:
    """Simule fetch_one / execute pour MariaDbSessionStore sans MariaDB réelle."""

    def __init__(self):
        # {session_id: {"data": json_str, "expire_ts": float}}
        self.rows: dict[str, dict] = {}

    def fetch_one(self, sql: str, params: tuple) -> dict | None:
        sid = params[0] if params else None
        row = self.rows.get(sid)
        if row is None:
            return None
        # Simule expire_at > NOW() quand la clause est présente dans la requête
        if "expire_at > NOW()" in sql and row["expire_ts"] < time.time():
            return None
        return {"data": row["data"]}

    def execute(self, sql: str, params: tuple = ()) -> int:
        sql_s = sql.strip()
        # INSERT
        if sql_s.startswith("INSERT"):
            sid, data_json, expire_dt = params[0], params[1], params[2]
            expire_ts = datetime.strptime(expire_dt, "%Y-%m-%d %H:%M:%S").timestamp()
            self.rows[sid] = {"data": data_json, "expire_ts": expire_ts}
            return 1
        # UPDATE data
        if sql_s.startswith("UPDATE"):
            data_json, sid = params[0], params[1]
            if sid in self.rows:
                self.rows[sid]["data"] = data_json
                return 1
            return 0
        # DELETE par session_id
        if sql_s.startswith("DELETE") and "WHERE session_id" in sql:
            sid = params[0]
            return 1 if self.rows.pop(sid, None) is not None else 0
        # CLEANUP expiré
        if sql_s.startswith("DELETE") and "expire_at < NOW()" in sql:
            now = time.time()
            expired = [k for k, v in self.rows.items() if v["expire_ts"] < now]
            for k in expired:
                del self.rows[k]
            return len(expired)
        return 0


# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_store(ttl: int = 3600):
    from core.sessions.mariadb_store import MariaDbSessionStore
    db = _FakeDB()
    store = MariaDbSessionStore(fetch_one=db.fetch_one, execute=db.execute, ttl=ttl)
    return store, db


# ── Importabilité ─────────────────────────────────────────────────────────────


def test_mariadb_store_importable():
    from core.sessions.mariadb_store import MariaDbSessionStore
    assert callable(MariaDbSessionStore)


def test_mariadb_store_importable_from_core_sessions():
    from core.sessions import MariaDbSessionStore
    assert callable(MariaDbSessionStore)


def test_mariadb_store_implements_protocol():
    from core.sessions import SessionStore
    store, _ = _make_store()
    assert isinstance(store, SessionStore)


def test_sql_file_exists():
    assert (ROOT / "mvc" / "models" / "sql" / "forge_sessions.sql").exists()


def test_sql_file_contains_create_table():
    sql = (ROOT / "mvc" / "models" / "sql" / "forge_sessions.sql").read_text(encoding="utf-8")
    assert "CREATE TABLE" in sql
    assert "forge_sessions" in sql


def test_sql_file_contains_session_id_primary_key():
    sql = (ROOT / "mvc" / "models" / "sql" / "forge_sessions.sql").read_text(encoding="utf-8")
    assert "session_id" in sql
    assert "PRIMARY KEY" in sql


def test_sql_file_contains_expire_at():
    sql = (ROOT / "mvc" / "models" / "sql" / "forge_sessions.sql").read_text(encoding="utf-8")
    assert "expire_at" in sql


# ── Création ──────────────────────────────────────────────────────────────────


def test_mariadb_store_create_returns_64_hex():
    store, _ = _make_store()
    sid = store.create()
    assert isinstance(sid, str)
    assert len(sid) == 64
    assert all(c in "0123456789abcdef" for c in sid)


def test_mariadb_store_create_inserts_row():
    store, db = _make_store()
    sid = store.create()
    assert sid in db.rows


def test_mariadb_store_create_standard_structure():
    store, _ = _make_store()
    sid = store.create()
    data = store.get(sid)
    assert data is not None
    assert data["authenticated"] is False
    assert data["user"] is None
    assert "csrf_token" in data
    assert "expires_at" in data


def test_mariadb_store_create_data_is_json():
    store, db = _make_store()
    sid = store.create()
    raw = json.loads(db.rows[sid]["data"])
    assert isinstance(raw, dict)


# ── Lecture ───────────────────────────────────────────────────────────────────


def test_mariadb_store_get_returns_data():
    store, _ = _make_store()
    sid = store.create()
    assert store.get(sid) is not None


def test_mariadb_store_get_unknown_returns_none():
    store, _ = _make_store()
    assert store.get("a" * 64) is None


def test_mariadb_store_get_invalid_id_returns_none():
    store, _ = _make_store()
    assert store.get("invalid") is None


def test_mariadb_store_get_empty_returns_none():
    store, _ = _make_store()
    assert store.get("") is None


def test_mariadb_store_get_invalid_no_sql_call():
    """Un session_id invalide est rejeté avant toute requête SQL."""
    calls = []

    def fake_fetch(sql, params):
        calls.append(sql)
        return None

    def fake_run(sql, params=()):
        calls.append(sql)
        return 0

    from core.sessions.mariadb_store import MariaDbSessionStore
    store = MariaDbSessionStore(fetch_one=fake_fetch, execute=fake_run)
    store.get("../bad/../id")
    store.get("")
    store.get("G" * 64)
    assert calls == []


# ── Modification ──────────────────────────────────────────────────────────────


def test_mariadb_store_set_updates_data():
    store, _ = _make_store()
    sid = store.create()
    store.set(sid, {"custom_key": "custom_value"})
    data = store.get(sid)
    assert data is not None
    assert data["custom_key"] == "custom_value"
    assert data["authenticated"] is False


def test_mariadb_store_set_unknown_is_noop():
    store, db = _make_store()
    store.set("a" * 64, {"x": 1})
    assert "a" * 64 not in db.rows


def test_mariadb_store_set_invalid_id_no_sql_call():
    calls = []

    def fake_fetch(sql, params):
        calls.append(sql)
        return None

    def fake_run(sql, params=()):
        calls.append(sql)
        return 0

    from core.sessions.mariadb_store import MariaDbSessionStore
    store = MariaDbSessionStore(fetch_one=fake_fetch, execute=fake_run)
    store.set("not-valid", {"x": 1})
    assert calls == []


# ── Suppression ───────────────────────────────────────────────────────────────


def test_mariadb_store_delete_removes_session():
    store, db = _make_store()
    sid = store.create()
    store.delete(sid)
    assert store.get(sid) is None
    assert sid not in db.rows


def test_mariadb_store_delete_unknown_is_noop():
    store, _ = _make_store()
    store.delete("a" * 64)


def test_mariadb_store_delete_invalid_id_no_sql_call():
    calls = []

    def fake_run(sql, params=()):
        calls.append(sql)
        return 0

    from core.sessions.mariadb_store import MariaDbSessionStore
    store = MariaDbSessionStore(fetch_one=lambda s, p: None, execute=fake_run)
    store.delete("not-valid")
    assert calls == []


# ── Régénération ──────────────────────────────────────────────────────────────


def test_mariadb_store_regenerate_returns_new_id():
    store, _ = _make_store()
    sid = store.create()
    nouveau = store.regenerate(sid)
    assert nouveau != sid
    assert len(nouveau) == 64


def test_mariadb_store_regenerate_preserves_data():
    store, _ = _make_store()
    sid = store.create()
    store.set(sid, {"user_key": "user_val"})
    nouveau = store.regenerate(sid)
    data = store.get(nouveau)
    assert data is not None
    assert data["user_key"] == "user_val"


def test_mariadb_store_regenerate_old_id_gone():
    store, db = _make_store()
    sid = store.create()
    store.regenerate(sid)
    assert store.get(sid) is None
    assert sid not in db.rows


# ── Expiration ────────────────────────────────────────────────────────────────


def test_mariadb_store_expired_returns_none():
    store, _ = _make_store(ttl=0)
    sid = store.create()
    time.sleep(0.01)
    assert store.get(sid) is None


def test_mariadb_store_set_on_expired_is_noop():
    store, db = _make_store(ttl=0)
    sid = store.create()
    time.sleep(0.01)
    store.set(sid, {"x": 1})
    data = json.loads(db.rows[sid]["data"])
    assert "x" not in data


# ── Nettoyage ─────────────────────────────────────────────────────────────────


def test_mariadb_store_cleanup_removes_expired():
    store, db = _make_store(ttl=0)
    store.create()
    store.create()
    time.sleep(0.01)
    count = store.cleanup_expired()
    assert count == 2
    assert db.rows == {}


def test_mariadb_store_cleanup_keeps_valid():
    store_short, db = _make_store(ttl=0)
    store_long, _ = _make_store(ttl=3600)
    store_long._execute = db.execute
    store_long._fetch_one = db.fetch_one
    store_short.create()
    sid_valid = store_long.create()
    time.sleep(0.01)
    store_short.cleanup_expired()
    assert sid_valid in db.rows


def test_mariadb_store_cleanup_empty_returns_zero():
    store, _ = _make_store()
    assert store.cleanup_expired() == 0


def test_mariadb_store_cleanup_returns_count():
    store, _ = _make_store(ttl=0)
    for _ in range(4):
        store.create()
    time.sleep(0.01)
    assert store.cleanup_expired() == 4


# ── JSON corrompu ─────────────────────────────────────────────────────────────


def test_mariadb_store_corrupted_json_returns_none():
    store, db = _make_store()
    sid = store.create()
    db.rows[sid]["data"] = "not json"
    assert store.get(sid) is None


def test_mariadb_store_corrupted_json_no_exception():
    store, db = _make_store()
    sid = store.create()
    db.rows[sid]["data"] = "{bad: json}"
    try:
        result = store.get(sid)
        assert result is None
    except Exception as exc:
        raise AssertionError(f"get() a levé une exception sur JSON corrompu : {exc}") from exc


def test_mariadb_store_wrong_type_returns_none():
    store, db = _make_store()
    sid = store.create()
    db.rows[sid]["data"] = '["liste", "pas", "dict"]'
    assert store.get(sid) is None


def test_mariadb_store_corrupted_deletes_row():
    """Une session corrompue est supprimée lors de la lecture."""
    deleted = []

    def fake_fetch(sql, params):
        return {"data": "invalid json{{{"}

    def fake_run(sql, params=()):
        if "WHERE session_id" in sql:
            deleted.append(params[0] if params else None)
        return 0

    from core.sessions.mariadb_store import MariaDbSessionStore
    store = MariaDbSessionStore(fetch_one=fake_fetch, execute=fake_run, ttl=3600)
    result = store.get("a" * 64)
    assert result is None
    assert len(deleted) == 1


# ── Données JSON sérialisables ────────────────────────────────────────────────


def test_mariadb_store_data_is_json_serializable():
    store, db = _make_store()
    sid = store.create()
    raw = db.rows[sid]["data"]
    parsed = json.loads(raw)
    assert isinstance(parsed, dict)


# ── Sérialiseurs interdits ────────────────────────────────────────────────────

_BANNED_WORDS = ["pic" + "kle", "mar" + "shal", "ev" + "al(", "ex" + "ec("]


def test_banned_serializers_absent_from_mariadb_store():
    source = (ROOT / "core" / "sessions" / "mariadb_store.py").read_text(encoding="utf-8")
    for word in _BANNED_WORDS:
        assert word not in source, f"mot interdit dans mariadb_store.py : {word}"


def test_banned_serializers_absent_from_this_test():
    source = Path(__file__).read_text(encoding="utf-8")
    for word in _BANNED_WORDS:
        assert word not in source, f"mot interdit dans le fichier de test : {word}"


# ── Backend par défaut inchangé ───────────────────────────────────────────────


def test_default_store_is_still_memory_store():
    from core.sessions import get_session_store, MemorySessionStore
    assert isinstance(get_session_store(), MemorySessionStore)


# ── Roadmap ───────────────────────────────────────────────────────────────────


def test_roadmap_reference_session_mariadb_store_001():
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "SESSION-MARIADB-STORE-001" in content
