"""Tests SESSIONS-CONTRACT-001 — intégration du contrat de session sur les trois backends.

Chaque test du scénario complet s'exécute sur MemorySessionStore et FileSessionStore.
MariaDbSessionStore utilise des callables injectés (pas de connexion réelle requise).
"""

from __future__ import annotations

import pytest

from core.sessions.memory_store import MemorySessionStore
from core.sessions.file_store import FileSessionStore
from core.sessions.mariadb_store import MariaDbSessionStore


# ── Fixture commune — instancie le store selon le paramètre ──────────────────

@pytest.fixture(params=["memory", "file", "mariadb"])
def store(request, tmp_path):
    if request.param == "memory":
        return MemorySessionStore()
    if request.param == "file":
        return FileSessionStore(sessions_dir=str(tmp_path / "sessions"))
    # mariadb — store en mémoire simulé via callables injectés
    _db: dict[str, dict] = {}

    def _fetch_one(sql, params):
        sid = params[0]
        row = _db.get(sid)
        return {"data": __import__("json").dumps(row)} if row else None

    def _execute(sql, params=()):
        import json as _json
        sql_up = sql.strip().upper()
        if sql_up.startswith("INSERT"):
            sid, data_json = params[0], params[1]
            _db[sid] = _json.loads(data_json)
        elif sql_up.startswith("UPDATE") and "expire_at" in sql.lower():
            data_json, _expire, sid = params[0], params[1], params[2]
            if sid in _db:
                _db[sid] = _json.loads(data_json)
        elif sql_up.startswith("UPDATE"):
            data_json, sid = params[0], params[1]
            if sid in _db:
                _db[sid] = _json.loads(data_json)
        elif sql_up.startswith("DELETE"):
            sid = params[0]
            _db.pop(sid, None)
        return 1

    return MariaDbSessionStore(fetch_one=_fetch_one, execute=_execute)


# ── Scénario complet ──────────────────────────────────────────────────────────

def test_full_session_lifecycle(store):
    """Création → authentification → flash (set+get+consommé) → touch_expiry → suppression."""
    sid = store.create()
    assert store.get(sid) is not None

    user_data = {"id": 1, "login": "alice", "prenom": "Alice", "nom": "D", "email": "", "roles": []}
    new_sid = store.authenticate(sid, user_data, ttl_seconds=3600)
    assert new_sid is not None
    assert new_sid != sid
    assert store.get(sid) is None, "L'ancienne session doit être invalidée"

    session = store.get(new_sid)
    assert session is not None
    assert session["authenticated"] is True
    assert session["user"]["login"] == "alice"
    assert "csrf_token" in session

    assert store.set_flash(new_sid, "Bienvenue", "success") is True
    flash = store.get_flash(new_sid)
    assert flash == {"message": "Bienvenue", "level": "success"}
    assert store.get_flash(new_sid) is None, "Le flash doit être consommé après lecture"

    assert store.touch_expiry(new_sid, ttl_seconds=7200) is True

    store.delete(new_sid)
    assert store.get(new_sid) is None


def test_operations_on_missing_session_return_safely(store):
    """Toutes les opérations sur un session_id inexistant retournent sans lever."""
    fake = "a" * 64
    assert store.get(fake) is None
    assert store.set_flash(fake, "x") is False
    assert store.get_flash(fake) is None
    assert store.touch_expiry(fake, 60) is False
    assert store.authenticate(fake, {"id": 1}, 60) is None


def test_set_flash_puis_get_flash_consomme(store):
    """get_flash consomme le flash : un second appel retourne None."""
    sid = store.create()
    store.set_flash(sid, "Test", "info")
    assert store.get_flash(sid) is not None
    assert store.get_flash(sid) is None


def test_authenticate_invalide_ancienne_session(store):
    """Après authenticate(), l'ancien session_id n'est plus valide."""
    sid = store.create()
    new_sid = store.authenticate(sid, {"id": 42, "login": "bob", "roles": []}, 3600)
    assert new_sid is not None
    assert store.get(sid) is None


def test_touch_expiry_session_inconnue(store):
    """touch_expiry retourne False si la session n'existe pas."""
    assert store.touch_expiry("b" * 64, 3600) is False


# ── Contrat : les stores implémentent bien le Protocol ───────────────────────

def test_memory_store_implements_protocol():
    from core.sessions.contract import SessionStore
    assert isinstance(MemorySessionStore(), SessionStore)


def test_file_store_implements_protocol(tmp_path):
    from core.sessions.contract import SessionStore
    assert isinstance(FileSessionStore(sessions_dir=str(tmp_path)), SessionStore)
