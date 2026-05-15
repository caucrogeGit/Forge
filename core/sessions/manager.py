"""Gestionnaire de backend de session Forge."""

from __future__ import annotations

from core.sessions.contract import SessionStore
from core.sessions.memory_store import MemorySessionStore

_default_store: MemorySessionStore = MemorySessionStore()


def get_session_store() -> SessionStore:
    """Retourne le backend de session actif (MemorySessionStore par défaut)."""
    return _default_store
