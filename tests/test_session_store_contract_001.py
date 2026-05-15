"""Tests pour SESSION-STORE-CONTRACT-001 — Contrat de backend de session."""

from __future__ import annotations

import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


# ── Imports publics ───────────────────────────────────────────────────────────


def test_session_store_protocol_importable():
    """core.sessions.SessionStore est importable."""
    from core.sessions import SessionStore
    assert SessionStore is not None


def test_memory_session_store_importable():
    """core.sessions.MemorySessionStore est importable."""
    from core.sessions import MemorySessionStore
    assert callable(MemorySessionStore)


def test_get_session_store_importable():
    """core.sessions.get_session_store est importable."""
    from core.sessions import get_session_store
    assert callable(get_session_store)


def test_memory_store_implements_protocol():
    """MemorySessionStore est une instance de SessionStore (runtime_checkable)."""
    from core.sessions import MemorySessionStore, SessionStore
    store = MemorySessionStore()
    assert isinstance(store, SessionStore)


# ── MemorySessionStore : CRUD de base ─────────────────────────────────────────


def test_memory_store_create_returns_session_id():
    """create() retourne un session_id de 64 caractères hex."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    assert isinstance(sid, str)
    assert len(sid) == 64
    assert all(c in "0123456789abcdef" for c in sid)


def test_memory_store_get_created_session():
    """get() retourne les données de la session créée."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    data = store.get(sid)
    assert data is not None
    assert data["authenticated"] is False
    assert data["user"] is None
    assert "csrf_token" in data
    assert "expires_at" in data


def test_memory_store_get_unknown_returns_none():
    """get() retourne None pour un session_id inexistant."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    assert store.get("inexistant" * 4) is None


def test_memory_store_set_updates_data():
    """set() met à jour les données d'une session existante."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    store.set(sid, {"custom_key": "custom_value"})
    data = store.get(sid)
    assert data is not None
    assert data["custom_key"] == "custom_value"
    assert data["authenticated"] is False  # les champs existants sont préservés


def test_memory_store_set_unknown_is_noop():
    """set() sur un session_id inexistant ne lève pas d'erreur."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    store.set("inexistant" * 4, {"x": 1})  # ne doit pas lever


def test_memory_store_delete_removes_session():
    """delete() supprime la session."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    store.delete(sid)
    assert store.get(sid) is None


def test_memory_store_delete_unknown_is_noop():
    """delete() sur un session_id inexistant ne lève pas d'erreur."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    store.delete("inexistant" * 4)  # ne doit pas lever


def test_memory_store_regenerate_returns_new_id():
    """regenerate() retourne un nouveau session_id différent."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    nouveau = store.regenerate(sid)
    assert nouveau != sid
    assert len(nouveau) == 64


def test_memory_store_regenerate_preserves_data():
    """regenerate() conserve les données de session."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    store.set(sid, {"user_key": "user_val"})
    nouveau = store.regenerate(sid)
    data = store.get(nouveau)
    assert data is not None
    assert data["user_key"] == "user_val"


def test_memory_store_regenerate_old_id_gone():
    """Après regenerate(), l'ancien session_id n'est plus valide."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    sid = store.create()
    store.regenerate(sid)
    assert store.get(sid) is None


# ── Expiration ────────────────────────────────────────────────────────────────


def test_memory_store_expired_session_returns_none():
    """get() retourne None pour une session expirée."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore(ttl=0)
    sid = store.create()
    time.sleep(0.01)
    assert store.get(sid) is None


# ── Thread-safety ─────────────────────────────────────────────────────────────


def test_memory_store_thread_safe_create():
    """create() est thread-safe : 50 sessions créées en parallèle."""
    from core.sessions import MemorySessionStore
    store = MemorySessionStore()
    ids = []
    lock = threading.Lock()

    def worker():
        sid = store.create()
        with lock:
            ids.append(sid)

    threads = [threading.Thread(target=worker) for _ in range(50)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(ids) == 50
    assert len(set(ids)) == 50  # tous uniques


# ── Compatibilité backward core.security.session ─────────────────────────────


def test_security_session_create_session_works():
    """core.security.session.create_session() fonctionne encore."""
    from core.security.session import create_session, get_session
    sid = create_session()
    assert get_session(sid) is not None


def test_security_session_delete_session_works():
    """core.security.session.delete_session() fonctionne encore."""
    from core.security.session import create_session, get_session, delete_session
    sid = create_session()
    delete_session(sid)
    assert get_session(sid) is None


def test_security_session_regenerate_session_works():
    """core.security.session.regenerate_session() fonctionne encore."""
    from core.security.session import create_session, get_session, regenerate_session
    sid = create_session()
    nouveau = regenerate_session(sid)
    assert nouveau != sid
    assert get_session(sid) is None
    assert get_session(nouveau) is not None


def test_security_session_public_api_importable():
    """Toutes les fonctions publiques de core.security.session restent importables."""
    from core.security.session import (
        create_session,
        get_session,
        delete_session,
        regenerate_session,
        authenticate_session,
        get_session_id,
        is_authenticated,
        get_user,
        user_has_role,
        set_flash,
        get_flash,
    )
    for fn in (
        create_session, get_session, delete_session, regenerate_session,
        authenticate_session, get_session_id, is_authenticated, get_user,
        user_has_role, set_flash, get_flash,
    ):
        assert callable(fn)


def test_auth_session_public_api_importable():
    """Toutes les fonctions publiques de core.auth.session restent importables."""
    from core.auth.session import (
        authenticate_user,
        login_user,
        logout_user,
        get_authenticated_user_id,
        current_user,
        is_authenticated,
        login_required,
    )
    for fn in (
        authenticate_user, login_user, logout_user,
        get_authenticated_user_id, current_user, is_authenticated, login_required,
    ):
        assert callable(fn)


def test_manager_default_store_est_memory_store():
    """get_session_store() retourne une instance de MemorySessionStore."""
    from core.sessions import get_session_store, MemorySessionStore
    store = get_session_store()
    assert isinstance(store, MemorySessionStore)


# ── Roadmap ───────────────────────────────────────────────────────────────────


def test_roadmap_reference_session_store_contract_001():
    """forge-roadmap.md référence SESSION-STORE-CONTRACT-001."""
    content = (ROOT / "docs" / "roadmap" / "forge-roadmap.md").read_text(encoding="utf-8")
    assert "SESSION-STORE-CONTRACT-001" in content
