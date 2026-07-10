"""Tests — SESSION-CLEANUP-AUTO-001.

Verrouille le nettoyage automatique des sessions expirées :

  * `MemorySessionStore.cleanup_expired()` retourne le nombre de sessions
    supprimées et préserve les sessions valides ;
  * le cleanup opportuniste préexistant (lazy via `get()`, balayage
    global via `create()`) continue de fonctionner ;
  * aucun thread, scheduler ou timer global n'est introduit ;
  * les autres stores Forge (`FileSessionStore`, `DbSessionStore`)
    exposent la même API pour qu'un opérateur cron applicatif puisse
    appeler `cleanup_expired()` uniformément.
"""
from __future__ import annotations

import threading

from core.sessions.memory_store import MemorySessionStore


# ── Helpers : maîtrise du temps via injection de TTL ────────────────────────


def _expire_session(store: MemorySessionStore, session_id: str) -> None:
    """Force l'expiration d'une session sans manipuler `time.time()`.

    Réécrit `expires_at` dans le passé. C'est plus stable qu'un
    monkeypatch global de l'horloge (qui interfère avec
    `secrets.token_hex`, le logging, etc.).
    """
    with store._lock:
        store._sessions[session_id]["expires_at"] = 0


# ── 1. cleanup_expired : API publique ───────────────────────────────────────


class TestCleanupExpiredApi:
    def test_returns_zero_on_empty_store(self):
        store = MemorySessionStore()
        assert store.cleanup_expired() == 0

    def test_returns_zero_when_all_valid(self):
        store = MemorySessionStore()
        store.create()
        store.create()
        store.create()
        assert store.cleanup_expired() == 0

    def test_removes_only_expired_sessions(self):
        store = MemorySessionStore()
        valid_a = store.create()
        expired_a = store.create()
        expired_b = store.create()
        valid_b = store.create()
        _expire_session(store, expired_a)
        _expire_session(store, expired_b)

        removed = store.cleanup_expired()

        assert removed == 2
        # Valides intactes
        assert store.get(valid_a) is not None
        assert store.get(valid_b) is not None
        # Expirées disparues
        assert store.get(expired_a) is None
        assert store.get(expired_b) is None

    def test_many_expired_sessions(self):
        store = MemorySessionStore()
        ids = [store.create() for _ in range(20)]
        for sid in ids[:15]:
            _expire_session(store, sid)
        assert store.cleanup_expired() == 15
        for sid in ids[15:]:
            assert store.get(sid) is not None


# ── 2. Cleanup opportuniste préexistant préservé ────────────────────────────


class TestOpportunisticCleanupPreserved:
    def test_get_on_expired_session_returns_none_and_removes(self):
        store = MemorySessionStore()
        sid = store.create()
        _expire_session(store, sid)
        assert store.get(sid) is None
        # L'entrée doit avoir été retirée par get() (lazy cleanup).
        assert sid not in store._sessions

    def test_create_triggers_global_cleanup(self):
        store = MemorySessionStore()
        expired = store.create()
        _expire_session(store, expired)
        # Création d'une nouvelle session → _cleanup() global déclenché
        store.create()
        assert expired not in store._sessions


# ── 3. Pas de thread / timer ajouté ─────────────────────────────────────────


class TestNoBackgroundActivity:
    def test_no_thread_started_by_construction(self):
        """Aucun thread Forge ne tourne pour le cleanup."""
        baseline = {t.ident for t in threading.enumerate()}
        store = MemorySessionStore()
        for _ in range(5):
            store.create()
        store.cleanup_expired()
        after = {t.ident for t in threading.enumerate()}
        assert after == baseline


# ── 4. Cohérence avec les autres stores ─────────────────────────────────────


class TestApiAlignmentAcrossStores:
    """Les 3 stores doivent exposer `cleanup_expired() -> int` callable."""

    def test_memory_store_has_cleanup_expired(self):
        store = MemorySessionStore()
        assert callable(getattr(store, "cleanup_expired", None))
        result = store.cleanup_expired()
        assert isinstance(result, int)

    def test_file_store_has_cleanup_expired(self):
        from core.sessions.file_store import FileSessionStore
        assert callable(getattr(FileSessionStore, "cleanup_expired", None))

    def test_db_store_has_cleanup_expired(self):
        import pytest
        DbSessionStore = pytest.importorskip("forge_mvc_sessions_db").DbSessionStore
        assert callable(getattr(DbSessionStore, "cleanup_expired", None))


# ── 5. Pas de mutation cookies / autres données ─────────────────────────────


class TestNoSideEffectsOnUnrelatedData:
    def test_csrf_token_of_valid_session_unchanged(self):
        store = MemorySessionStore()
        sid_valid = store.create()
        token_before = store.get(sid_valid)["csrf_token"]
        sid_expired = store.create()
        _expire_session(store, sid_expired)
        store.cleanup_expired()
        token_after = store.get(sid_valid)["csrf_token"]
        assert token_before == token_after

    def test_user_data_of_valid_session_unchanged(self):
        store = MemorySessionStore()
        sid = store.create({"hello": "world"})
        store.create()  # une autre session pour avoir du trafic
        _expire_session(store, store.create())  # créer puis expirer
        store.cleanup_expired()
        data = store.get(sid)
        assert data is not None
        assert data.get("hello") == "world"


# ── 6. Comportement public préservé (sanity) ────────────────────────────────


class TestPublicBehaviorPreserved:
    def test_valid_session_still_readable(self):
        store = MemorySessionStore()
        sid = store.create({"k": 1})
        data = store.get(sid)
        assert data is not None and data["k"] == 1

    def test_logout_via_delete_unchanged(self):
        store = MemorySessionStore()
        sid = store.create()
        store.delete(sid)
        assert store.get(sid) is None
