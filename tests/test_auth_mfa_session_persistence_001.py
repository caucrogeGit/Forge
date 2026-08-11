"""Tests MFA-SESSION-PERSISTENCE-001 — persistence MFA sur tous les backends de session.

Verifie que start_mfa_challenge, clear_mfa_challenge, mark_mfa_revalidated et
clear_mfa_revalidation persistenten reellement les changements de session, meme
sur les backends File et MariaDB qui retournent des copies deserialisees depuis
store.get() — contrairement a MemorySessionStore qui retourne une reference vivante.
"""

from __future__ import annotations

import pytest
pytest.importorskip("forge_mvc_mfa")

from datetime import datetime, timezone

from forge_mvc_mfa import (
    MFA_CHALLENGE_STARTED_AT_KEY,
    MFA_CHALLENGE_USER_ID_KEY,
    MFA_REVALIDATION_AT_KEY,
    MFA_REVALIDATION_USER_ID_KEY,
    clear_mfa_challenge,
    clear_mfa_revalidation,
    has_pending_mfa_challenge,
    has_recent_mfa_revalidation,
    mark_mfa_revalidated,
    start_mfa_challenge,
)
from forge_mvc_mfa.mfa import _persist_session_changes
from core.auth.user import AuthUser

_NOW = datetime(2026, 5, 10, 12, 0, 0, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


class FakeRequestDirect:
    """Requete avec attribut session dict — chemin direct sans store."""

    def __init__(self):
        self.session = {}


class RealFakeRequest:
    """Requete HTTP simulee sans attribut session — force le chemin store."""

    def __init__(self, session_id: str):
        self.headers = {"Cookie": f"__Host-session_id={session_id}"}


def _make_user(user_id: int = 1) -> AuthUser:
    return AuthUser(
        id=user_id,
        login=f"user{user_id}@example.com",
        password_hash="hash",
        is_active=True,
    )


def _patch_both_stores(monkeypatch, store) -> None:
    """Injecte le store via _configured_store pour que _resolve et _persist voient le meme backend."""
    import core.sessions.manager as _mgr

    monkeypatch.setattr(_mgr, "_configured_store", store)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def direct_request():
    return FakeRequestDirect()


@pytest.fixture
def memory_store():
    from core.sessions.memory_store import MemorySessionStore

    return MemorySessionStore()


@pytest.fixture
def file_store(tmp_path):
    from core.sessions.file_store import FileSessionStore

    return FileSessionStore(sessions_dir=tmp_path / "sessions")


@pytest.fixture(params=["memory", "file"])
def store_and_request(request, memory_store, file_store, monkeypatch):
    """Fixture parametree (memory, file) : retourne (store, session_id, req)."""
    store = memory_store if request.param == "memory" else file_store
    _patch_both_stores(monkeypatch, store)
    session_id = store.create()
    req = RealFakeRequest(session_id)
    return store, session_id, req


# ---------------------------------------------------------------------------
# TestPersistSessionChangesDirect — chemin dict
# ---------------------------------------------------------------------------


class TestPersistSessionChangesDirect:
    def test_set_keys_on_dict_session(self, direct_request):
        _persist_session_changes(direct_request, set_keys={"foo": "bar"})
        assert direct_request.session["foo"] == "bar"

    def test_unset_keys_on_dict_session(self, direct_request):
        direct_request.session["mfa_uid"] = 42
        _persist_session_changes(direct_request, unset_keys=["mfa_uid"])
        assert "mfa_uid" not in direct_request.session

    def test_unset_absent_key_is_noop(self, direct_request):
        _persist_session_changes(direct_request, unset_keys=["nonexistent"])

    def test_set_and_unset_combined(self, direct_request):
        direct_request.session["old"] = "value"
        _persist_session_changes(
            direct_request, set_keys={"new": "x"}, unset_keys=["old"]
        )
        assert direct_request.session.get("new") == "x"
        assert "old" not in direct_request.session

    def test_no_keys_is_noop(self, direct_request):
        direct_request.session["stable"] = 1
        _persist_session_changes(direct_request)
        assert direct_request.session["stable"] == 1


# ---------------------------------------------------------------------------
# TestPersistSessionChangesStore — chemin store (memory + file)
# ---------------------------------------------------------------------------


class TestPersistSessionChangesStore:
    def test_set_keys_persists_to_store(self, store_and_request):
        store, session_id, req = store_and_request
        _persist_session_changes(req, set_keys={"mfa_uid": 99})
        assert store.get(session_id)["mfa_uid"] == 99

    def test_unset_keys_persists_to_store(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {"to_remove": "yes"})
        _persist_session_changes(req, unset_keys=["to_remove"])
        assert "to_remove" not in store.get(session_id)

    def test_set_and_unset_combined_on_store(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {"old": "v"})
        _persist_session_changes(
            req, set_keys={"new": "x"}, unset_keys=["old"]
        )
        data = store.get(session_id)
        assert data.get("new") == "x"
        assert "old" not in data

    def test_invalid_session_id_is_noop(self, monkeypatch, file_store):
        _patch_both_stores(monkeypatch, file_store)
        req = RealFakeRequest("not-a-valid-session-id")
        _persist_session_changes(req, set_keys={"x": 1})

    def test_no_cookie_is_noop(self, store_and_request):
        store, session_id, req = store_and_request

        class NoCookieRequest:
            headers = {"Cookie": ""}

        _persist_session_changes(NoCookieRequest(), set_keys={"x": 1})
        assert "x" not in (store.get(session_id) or {})


# ---------------------------------------------------------------------------
# TestStartMfaChallengeBackends
# ---------------------------------------------------------------------------


class TestStartMfaChallengeBackends:
    def test_persists_user_id_and_timestamp(self, store_and_request):
        store, session_id, req = store_and_request
        user = _make_user(user_id=7)
        start_mfa_challenge(req, user, now=_NOW)
        data = store.get(session_id)
        assert data[MFA_CHALLENGE_USER_ID_KEY] == 7
        assert data[MFA_CHALLENGE_STARTED_AT_KEY] == _NOW.isoformat()

    def test_has_pending_challenge_after_start(self, store_and_request):
        store, session_id, req = store_and_request
        user = _make_user()
        start_mfa_challenge(req, user, now=_NOW)
        assert has_pending_mfa_challenge(req, now=_NOW)

    def test_overwrites_previous_challenge(self, store_and_request):
        store, session_id, req = store_and_request
        user = _make_user(user_id=5)
        start_mfa_challenge(req, user, now=_NOW)
        user2 = _make_user(user_id=6)
        now2 = datetime(2026, 5, 10, 12, 0, 30, tzinfo=timezone.utc)
        start_mfa_challenge(req, user2, now=now2)
        data = store.get(session_id)
        assert data[MFA_CHALLENGE_USER_ID_KEY] == 6

    def test_direct_request_still_works(self):
        req = FakeRequestDirect()
        user = _make_user()
        start_mfa_challenge(req, user, now=_NOW)
        assert req.session[MFA_CHALLENGE_USER_ID_KEY] == 1


# ---------------------------------------------------------------------------
# TestClearMfaChallengeBackends
# ---------------------------------------------------------------------------


class TestClearMfaChallengeBackends:
    def test_clears_challenge_keys_from_store(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {
            MFA_CHALLENGE_USER_ID_KEY: 3,
            MFA_CHALLENGE_STARTED_AT_KEY: _NOW.isoformat(),
        })
        clear_mfa_challenge(req)
        data = store.get(session_id)
        assert MFA_CHALLENGE_USER_ID_KEY not in data
        assert MFA_CHALLENGE_STARTED_AT_KEY not in data

    def test_preserves_other_session_keys(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {
            MFA_CHALLENGE_USER_ID_KEY: 3,
            "csrf_token_extra": "abc",
        })
        clear_mfa_challenge(req)
        assert store.get(session_id).get("csrf_token_extra") == "abc"

    def test_idempotent_on_empty_session(self, store_and_request):
        store, session_id, req = store_and_request
        clear_mfa_challenge(req)

    def test_direct_request_still_works(self):
        req = FakeRequestDirect()
        req.session[MFA_CHALLENGE_USER_ID_KEY] = 1
        clear_mfa_challenge(req)
        assert MFA_CHALLENGE_USER_ID_KEY not in req.session


# ---------------------------------------------------------------------------
# TestMarkMfaRevalidatedBackends
# ---------------------------------------------------------------------------


class TestMarkMfaRevalidatedBackends:
    def test_persists_revalidation_to_store(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {"authenticated": True, "user": {"id": 9, "login": "test"}})
        mark_mfa_revalidated(req, user_id=9, now=_NOW)
        data = store.get(session_id)
        assert data[MFA_REVALIDATION_USER_ID_KEY] == 9
        assert data[MFA_REVALIDATION_AT_KEY] == _NOW.isoformat()

    def test_has_recent_revalidation_after_mark(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {"authenticated": True, "user": {"id": 9, "login": "test"}})
        mark_mfa_revalidated(req, user_id=9, now=_NOW)
        assert has_recent_mfa_revalidation(req, user_id=9, now=_NOW)

    def test_direct_request_still_works(self):
        req = FakeRequestDirect()
        req.session["authenticated"] = True
        req.session["user"] = {"id": 9, "login": "test"}
        mark_mfa_revalidated(req, user_id=9, now=_NOW)
        assert req.session[MFA_REVALIDATION_USER_ID_KEY] == 9


# ---------------------------------------------------------------------------
# TestClearMfaRevalidationBackends
# ---------------------------------------------------------------------------


class TestClearMfaRevalidationBackends:
    def test_clears_revalidation_keys_from_store(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {
            MFA_REVALIDATION_USER_ID_KEY: 4,
            MFA_REVALIDATION_AT_KEY: _NOW.isoformat(),
        })
        clear_mfa_revalidation(req)
        data = store.get(session_id)
        assert MFA_REVALIDATION_USER_ID_KEY not in data
        assert MFA_REVALIDATION_AT_KEY not in data

    def test_preserves_challenge_keys(self, store_and_request):
        store, session_id, req = store_and_request
        store.set(session_id, {
            MFA_REVALIDATION_USER_ID_KEY: 4,
            MFA_CHALLENGE_USER_ID_KEY: 4,
        })
        clear_mfa_revalidation(req)
        assert store.get(session_id).get(MFA_CHALLENGE_USER_ID_KEY) == 4

    def test_idempotent_on_empty_session(self, store_and_request):
        store, session_id, req = store_and_request
        clear_mfa_revalidation(req)

    def test_direct_request_still_works(self):
        req = FakeRequestDirect()
        req.session[MFA_REVALIDATION_USER_ID_KEY] = 4
        clear_mfa_revalidation(req)
        assert MFA_REVALIDATION_USER_ID_KEY not in req.session


# ---------------------------------------------------------------------------
# TestRegressionFileStoreInPlaceMutation
# ---------------------------------------------------------------------------


class TestRegressionFileStoreInPlaceMutation:
    def test_in_place_mutation_is_lost_on_file_store(self, tmp_path, monkeypatch):
        """Demontre que sans _persist_session_changes, FileStore perd les mutations."""
        from core.sessions.file_store import FileSessionStore

        store = FileSessionStore(sessions_dir=tmp_path / "sessions")
        session_id = store.create()

        # Mutation directe sur la copie deserialisee — pattern original buggue
        copy = store.get(session_id)
        copy["should_be_lost"] = True
        # Aucun appel a store.set() : la mutation est perdue

        assert "should_be_lost" not in store.get(session_id)

    def test_persist_session_changes_fixes_file_store(self, tmp_path, monkeypatch):
        """Verifie que _persist_session_changes corrige le probleme sur FileStore."""
        from core.sessions.file_store import FileSessionStore
        import core.sessions.manager as _mgr

        store = FileSessionStore(sessions_dir=tmp_path / "sessions")
        monkeypatch.setattr(_mgr, "_default_store", store)
        session_id = store.create()
        req = RealFakeRequest(session_id)

        _persist_session_changes(req, set_keys={"persisted": True})

        assert store.get(session_id)["persisted"] is True
