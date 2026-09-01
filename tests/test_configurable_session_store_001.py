"""Tests comportementaux — SESSIONS-CONFIGURABLE-STORE-001.

Prouve que forge.configure(session_store=...) est réellement utilisé par le flux session.
Aucune dépendance MariaDB requise.
"""
from __future__ import annotations

import pytest

import core.forge as forge
from core.sessions.manager import get_session_store, set_session_store
from core.sessions.memory_store import MemorySessionStore


# ---------------------------------------------------------------------------
# Fake store avec compteurs d'appels
# ---------------------------------------------------------------------------

class FakeSessionStore:
    """Fake store comptant les appels — prouve que le store injecté est utilisé."""

    def __init__(self) -> None:
        self.calls: list[str] = []
        self._data: dict[str, dict] = {}
        self._next_id = "fake-session-id-0000000000000000000000000000000000000000000000000000000000000000"

    def create(self, data: dict | None = None) -> str:
        self.calls.append("create")
        self._data[self._next_id] = data or {}
        return self._next_id

    def get(self, session_id: str) -> dict | None:
        self.calls.append("get")
        return self._data.get(session_id)

    def set(self, session_id: str, data: dict) -> None:
        self.calls.append("set")
        if session_id in self._data:
            self._data[session_id].update(data)

    def replace(self, session_id: str, data: dict) -> None:
        self.calls.append("replace")
        self._data[session_id] = data

    def delete(self, session_id: str) -> None:
        self.calls.append("delete")
        self._data.pop(session_id, None)

    def list_for_user(
        self, user_id: object, *, current_session_id: "str | None" = None
    ) -> list:
        """Résumés des sessions du compte (ADMIN-SESSIONS-VIEW-001).

        Le contrat est `runtime_checkable` : un store auquel il manque une
        méthode n'est plus reconnu, et `forge.configure` le refuse.
        """
        from core.sessions.contract import HANDLE_LENGTH, SessionSummary

        self.calls.append("list_for_user")
        return [
            SessionSummary(
                handle=sid[:HANDLE_LENGTH],
                is_current=sid == current_session_id,
            )
            for sid, data in self._data.items()
            if data.get("_auth_user_id") == user_id
        ]

    def delete_for_user(self, user_id: object) -> int:
        """Révocation par compte (SESSIONS-DELETE-FOR-USER-001).

        Le contrat est `runtime_checkable` : un store auquel il manque une
        méthode n'est plus reconnu, et `forge.configure` le refuse.
        """
        self.calls.append("delete_for_user")
        vises = [
            sid for sid, data in self._data.items()
            if data.get("_auth_user_id") == user_id
        ]
        for sid in vises:
            self._data.pop(sid, None)
        return len(vises)

    def regenerate(self, session_id: str) -> str:
        self.calls.append("regenerate")
        return session_id

    def authenticate(self, session_id: str, user_data: dict, ttl_seconds: int) -> str | None:
        self.calls.append("authenticate")
        return session_id

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        self.calls.append("touch_expiry")
        return True

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        self.calls.append("set_flash")
        return True

    def get_flash(self, session_id: str) -> dict | None:
        self.calls.append("get_flash")
        return None


# ---------------------------------------------------------------------------
# Fixture d'isolation — réinitialise le store après chaque test
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_session_store():
    """Réinitialise le store configuré avant et après chaque test."""
    set_session_store(None)
    yield
    set_session_store(None)


# ---------------------------------------------------------------------------
# Tests : configure(session_store=...) enregistre le store
# ---------------------------------------------------------------------------

class TestConfigureRegistersStore:

    def test_default_store_is_memory(self):
        """Sans configure, get_session_store() retourne un MemorySessionStore."""
        assert isinstance(get_session_store(), MemorySessionStore)

    def test_configure_registers_fake_store(self):
        """forge.configure(session_store=fake) enregistre le store dans le manager."""
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        assert get_session_store() is fake

    def test_configure_none_resets_to_default(self):
        """forge.configure(session_store=None) réinitialise au MemorySessionStore."""
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        assert get_session_store() is fake
        forge.configure(session_store=None)
        assert isinstance(get_session_store(), MemorySessionStore)

    def test_configure_invalid_store_raises_type_error(self):
        """Un store qui n'implémente pas SessionStore lève TypeError."""
        with pytest.raises(TypeError, match="session_store"):
            forge.configure(session_store="not-a-store")

    def test_configure_invalid_store_int_raises_type_error(self):
        with pytest.raises(TypeError, match="session_store"):
            forge.configure(session_store=42)

    def test_configure_unknown_key_still_raises(self):
        """Les autres clés inconnues lèvent toujours KeyError."""
        with pytest.raises(KeyError):
            forge.configure(unknown_key="value")


# ---------------------------------------------------------------------------
# Tests : le store injecté est réellement utilisé par le flux session
# ---------------------------------------------------------------------------

class TestInjectedStoreIsUsedByFlux:
    """Prouve que le store configuré est appelé lors des opérations de session."""

    def test_create_session_uses_injected_store(self):
        """create_session() passe par le store injecté."""
        from core.security.session import create_session
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        create_session()
        assert "create" in fake.calls

    def test_get_session_uses_injected_store(self):
        """get_session() passe par le store injecté."""
        from core.security.session import get_session
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        get_session("fake-session-id-0000000000000000000000000000000000000000000000000000000000000000")
        assert "get" in fake.calls

    def test_delete_session_uses_injected_store(self):
        """delete_session() passe par le store injecté."""
        from core.security.session import delete_session
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        delete_session("fake-session-id-0000000000000000000000000000000000000000000000000000000000000000")
        assert "delete" in fake.calls

    def test_set_flash_uses_injected_store(self):
        """set_flash() passe par le store injecté."""
        from core.security.session import set_flash
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        set_flash("fake-session-id-0000000000000000000000000000000000000000000000000000000000000000", "msg")
        assert "set_flash" in fake.calls

    def test_get_flash_uses_injected_store(self):
        """get_flash() passe par le store injecté."""
        from core.security.session import get_flash
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        get_flash("fake-session-id-0000000000000000000000000000000000000000000000000000000000000000")
        assert "get_flash" in fake.calls

    def test_default_store_still_works_without_configure(self):
        """Sans configure, le flux session utilise le MemorySessionStore."""
        from core.security.session import create_session, get_session
        sid = create_session()
        session = get_session(sid)
        assert session is not None

    def test_store_not_recreated_across_calls(self):
        """get_session_store() retourne le même objet à chaque appel."""
        fake = FakeSessionStore()
        forge.configure(session_store=fake)
        store1 = get_session_store()
        store2 = get_session_store()
        assert store1 is store2 is fake
