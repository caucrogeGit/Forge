"""Tests AUTH-LOGIN-PERSIST-001 — login_user/logout_user persistent dans le store.

Régression : `login_user` mutait le dict de session in-place sans appeler
`store.set()`. Sur MemorySessionStore (`get()` renvoie une référence vivante)
la mutation tenait, mais sur FileSessionStore et DbSessionStore (`get()`
renvoie une copie désérialisée) la connexion était silencieusement perdue —
le bug était masqué car le store par défaut est Memory.

Ces tests exercent le **chemin store** réel : une requête SANS attribut
`session` vivant, avec un cookie pointant vers une session du store configuré.
La persistance est ensuite vérifiée en relisant via `get_authenticated_user_id`
(qui recharge depuis le store), donc indépendamment de toute référence vivante.
"""

import os
from types import SimpleNamespace

import pytest

from core.auth import (
    AuthUser,
    get_authenticated_user_id,
    hash_password,
    login_user,
    logout_user,
)
from core.security.session import SESSION_COOKIE_NAME
from core.sessions.manager import set_session_store
from core.sessions.file_store import FileSessionStore
from core.sessions.memory_store import MemorySessionStore


def _active_user() -> AuthUser:
    return AuthUser(
        id=42,
        email="admin@example.test",
        password_hash=hash_password("secret123"),
        is_active=True,
    )


def _request_with_cookie(session_id: str):
    """Requête réaliste : cookie de session, AUCUN dict `session` vivant attaché."""
    return SimpleNamespace(headers={"Cookie": f"{SESSION_COOKIE_NAME}={session_id}"})


def _store_factories(tmp_path):
    """Liste (id, store) des backends à tester ; store BDD sous opt-in env."""
    factories = [
        ("memory", MemorySessionStore()),
        ("file", FileSessionStore(sessions_dir=tmp_path / "sessions")),
    ]
    if os.environ.get("FORGE_E2E_MARIADB"):
        from forge_mvc_sessions_db import DbSessionStore

        factories.append(("db", DbSessionStore()))
    return factories


@pytest.fixture(autouse=True)
def _reset_store():
    yield
    set_session_store(None)


def test_login_user_persists_across_all_stores(tmp_path):
    """login_user doit persister _auth_user_id sur CHAQUE backend, pas que Memory."""
    for store_id, store in _store_factories(tmp_path):
        set_session_store(store)
        session_id = store.create()
        request = _request_with_cookie(session_id)

        login_user(request, _active_user())

        # Relecture indépendante : un NOUVEAU request, même cookie.
        reread = _request_with_cookie(session_id)
        assert get_authenticated_user_id(reread) == 42, (
            f"backend {store_id} : connexion perdue après login_user "
            "(store.set non appelé ?)"
        )


def test_logout_user_persists_across_all_stores(tmp_path):
    """logout_user doit effacer _auth_user_id de façon persistante sur chaque backend."""
    for store_id, store in _store_factories(tmp_path):
        set_session_store(store)
        session_id = store.create()

        login_user(_request_with_cookie(session_id), _active_user())
        assert get_authenticated_user_id(_request_with_cookie(session_id)) == 42

        logout_user(_request_with_cookie(session_id))

        assert get_authenticated_user_id(_request_with_cookie(session_id)) is None, (
            f"backend {store_id} : déconnexion inopérante après logout_user "
            "(store.set non appelé ?)"
        )


def test_login_then_regenerate_preserves_user_id_file_store(tmp_path):
    """Reproduit le flux du contrôleur auth : login_user puis store.regenerate.

    regenerate recharge les données DEPUIS le store ; sans persistance dans
    login_user, _auth_user_id n'y serait pas et la connexion serait perdue
    après la rotation d'id (protection anti-fixation).
    """
    store = FileSessionStore(sessions_dir=tmp_path / "sessions")
    set_session_store(store)
    session_id = store.create()

    login_user(_request_with_cookie(session_id), _active_user())
    nouveau_id = store.regenerate(session_id)

    assert get_authenticated_user_id(_request_with_cookie(nouveau_id)) == 42
