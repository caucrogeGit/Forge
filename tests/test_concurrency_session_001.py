"""
Tests CONCURRENCY-SESSION-TESTS-001 — Concurrence sur les sessions Forge.

Vérifie que MemorySessionStore et les helpers session restent cohérents
sous accès concurrent simple (threads). Aucune base de données réelle,
aucun sleep fragile, aucun test de performance.

Règle : les tests valident l'absence d'exception et la cohérence des
données, pas l'ordre d'exécution des threads.
"""
from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import SimpleNamespace

from core.sessions.memory_store import MemorySessionStore

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_N = 50  # nombre de threads dans chaque test


def _fresh() -> MemorySessionStore:
    """Retourne un store neuf isolé du store global."""
    return MemorySessionStore()


def _req(session_id: str | None = None) -> SimpleNamespace:
    cookie = f"__Host-session_id={session_id}" if session_id else ""
    return SimpleNamespace(headers={"Cookie": cookie}, ip="127.0.0.1")


# ── Création concurrente ──────────────────────────────────────────────────────


def test_memory_store_creates_unique_sessions_concurrently():
    """N threads créent chacun une session — tous les IDs sont uniques et valides."""
    store = _fresh()
    ids = []

    def create_one(_):
        return store.create({"thread": True})

    with ThreadPoolExecutor(max_workers=_N) as pool:
        futures = [pool.submit(create_one, i) for i in range(_N)]
        ids = [f.result() for f in as_completed(futures)]

    assert len(ids) == _N
    assert len(set(ids)) == _N, "Des session_id dupliqués ont été générés"
    assert all(_HEX64.match(sid) for sid in ids), "Un session_id n'est pas au format 64 hex"
    assert len(store._sessions) == _N


def test_memory_store_creation_aucune_exception():
    """La création concurrente ne lève aucune exception."""
    store = _fresh()
    errors = []

    def create_one(_):
        try:
            store.create()
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(create_one, range(_N)))

    assert not errors, f"Exceptions levées : {errors}"


# ── Lectures concurrentes ─────────────────────────────────────────────────────


def test_memory_store_reads_session_concurrently():
    """N threads lisent la même session — données cohérentes, aucune exception."""
    store = _fresh()
    sid = store.create({"valeur": 42})
    results = []
    errors = []

    def read_one(_):
        try:
            data = store.get(sid)
            results.append(data)
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(read_one, range(_N)))

    assert not errors, f"Exceptions levées : {errors}"
    assert len(results) == _N
    for data in results:
        assert data is not None
        assert data["valeur"] == 42


def test_memory_store_reads_absent_session_concurrently():
    """N threads lisent une session inexistante — None retourné, aucune exception."""
    store = _fresh()
    errors = []
    results = []

    def read_one(_):
        try:
            results.append(store.get("session-qui-nexiste-pas"))
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(read_one, range(_N)))

    assert not errors
    assert all(r is None for r in results)


# ── Écritures concurrentes sur sessions distinctes ────────────────────────────


def test_memory_store_writes_distinct_sessions_concurrently():
    """N threads écrivent chacun sur leur propre session — pas de contamination."""
    store = _fresh()
    sessions = [(i, store.create({"proprietary": i})) for i in range(_N)]
    errors = []

    def write_one(args):
        i, sid = args
        try:
            store.set(sid, {"valeur": i * 10})
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(write_one, sessions))

    assert not errors, f"Exceptions levées : {errors}"
    for i, sid in sessions:
        data = store.get(sid)
        assert data is not None
        assert data["valeur"] == i * 10, f"Session {sid} : valeur contaminée"
        assert data["proprietary"] == i, f"Session {sid} : proprietary contaminé"


def test_memory_store_set_inexistante_silencieux():
    """Écriture sur une session inexistante — aucune exception, aucun effet."""
    store = _fresh()
    errors = []

    def write_one(_):
        try:
            store.set("session-fantome", {"x": 1})
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(write_one, range(_N)))

    assert not errors


# ── Suppressions et lectures concurrentes ────────────────────────────────────


def test_memory_store_deletes_sessions_concurrently():
    """Suppressions et lectures concurrentes — aucune exception, état cohérent."""
    store = _fresh()
    half = _N // 2
    to_delete = [store.create({"groupe": "delete"}) for _ in range(half)]
    to_keep = [store.create({"groupe": "keep"}) for _ in range(half)]
    errors = []

    def action(sid_and_op):
        sid, op = sid_and_op
        try:
            if op == "delete":
                store.delete(sid)
            else:
                store.get(sid)
        except Exception as exc:
            errors.append(exc)

    work = [(sid, "delete") for sid in to_delete] + [(sid, "read") for sid in to_keep]
    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(action, work))

    assert not errors
    for sid in to_delete:
        assert store.get(sid) is None, "Session supprimée encore présente"
    for sid in to_keep:
        data = store.get(sid)
        assert data is not None
        assert data["groupe"] == "keep"


def test_memory_store_double_delete_silencieux():
    """Supprimer la même session deux fois depuis des threads distincts — aucune exception."""
    store = _fresh()
    sid = store.create()
    errors = []

    def delete_one(_):
        try:
            store.delete(sid)
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(delete_one, range(_N)))

    assert not errors
    assert store.get(sid) is None


# ── Régénération concurrente ──────────────────────────────────────────────────


def test_memory_store_regenerates_session_ids_concurrently():
    """N threads régénèrent chacun leur propre session — nouveaux IDs valides et uniques."""
    store = _fresh()
    old_ids = [store.create({"index": i}) for i in range(_N)]
    new_ids = []
    errors = []

    def regen_one(sid):
        try:
            new_id = store.regenerate(sid)
            new_ids.append(new_id)
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(regen_one, old_ids))

    assert not errors
    assert len(new_ids) == _N
    assert len(set(new_ids)) == _N, "Des new session_id dupliqués ont été générés"
    assert all(_HEX64.match(sid) for sid in new_ids)
    for old_id in old_ids:
        assert store.get(old_id) is None, "Ancien session_id encore présent après régénération"


def test_memory_store_regenerate_preserve_donnees():
    """Régénération préserve les données de session sous accès concurrent."""
    store = _fresh()
    sids = [store.create({"token": i}) for i in range(_N)]
    results = {}
    errors = []

    def regen_and_read(args):
        i, sid = args
        try:
            new_sid = store.regenerate(sid)
            data = store.get(new_sid)
            results[i] = data
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(regen_and_read, enumerate(sids)))

    assert not errors
    for i, data in results.items():
        assert data is not None
        assert data.get("token") == i, f"Données perdues après régénération (session {i})"


# ── Helpers legacy (core/security/session.py) ────────────────────────────────


def test_legacy_session_helpers_work_under_concurrent_access():
    """create_session / get_session / delete_session sous accès concurrent."""
    from core.security.session import create_session, get_session, delete_session

    ids = []
    errors = []

    def create_one(_):
        try:
            sid = create_session()
            ids.append(sid)
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(create_one, range(_N)))

    assert not errors
    assert len(ids) == _N
    assert len(set(ids)) == _N

    errors.clear()

    def read_and_delete(sid):
        try:
            data = get_session(sid)
            assert data is not None
            delete_session(sid)
            assert get_session(sid) is None
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(read_and_delete, ids))

    assert not errors


def test_legacy_set_and_get_flash_concurrent():
    """set_flash / get_flash sous accès concurrent sur des sessions distinctes."""
    from core.security.session import create_session, set_flash, get_flash

    sids = [create_session() for _ in range(_N)]
    errors = []

    def flash_one(args):
        i, sid = args
        try:
            set_flash(sid, f"msg-{i}", "info")
            flash = get_flash(sid)
            assert flash is not None
            assert flash["message"] == f"msg-{i}"
            assert flash["level"] == "info"
            # Deuxième lecture : flash consommé
            assert get_flash(sid) is None
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(flash_one, enumerate(sids)))

    assert not errors


def test_legacy_regenerate_session_concurrent():
    """regenerate_session sous accès concurrent."""
    from core.security.session import create_session, regenerate_session, get_session

    old_ids = [create_session() for _ in range(_N)]
    new_ids = []
    errors = []

    def regen_one(sid):
        try:
            new_id = regenerate_session(sid)
            new_ids.append(new_id)
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(regen_one, old_ids))

    assert not errors
    assert len(set(new_ids)) == _N
    for old_id in old_ids:
        assert get_session(old_id) is None


def test_legacy_authenticate_session_concurrent():
    """authenticate_session sous accès concurrent sur des sessions distinctes."""
    from core.security.session import create_session, authenticate_session

    sids = [create_session() for _ in range(_N)]
    results = []
    errors = []

    _UTILISATEUR = {
        "UtilisateurId": 1,
        "Login": "user",
        "Prenom": "A",
        "Nom": "B",
        "Email": "a@b.fr",
        "roles": ["user"],
    }

    def auth_one(sid):
        try:
            new_sid = authenticate_session(sid, _UTILISATEUR)
            results.append(new_sid)
        except Exception as exc:
            errors.append(exc)

    with ThreadPoolExecutor(max_workers=_N) as pool:
        list(pool.map(auth_one, sids))

    assert not errors
    valid_results = [r for r in results if r is not None]
    assert len(valid_results) == _N
    assert len(set(valid_results)) == _N, "Des session_id authentifiés dupliqués"
