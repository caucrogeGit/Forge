# pyright: strict
"""Gestionnaire de backend de session Forge."""

from __future__ import annotations

from core.sessions.contract import SessionStore
from core.sessions.memory_store import MemorySessionStore

_default_store: MemorySessionStore = MemorySessionStore()
_configured_store: SessionStore | None = None


def get_session_store() -> SessionStore:
    """Retourne le backend de session actif.

    Si un store a été configuré via forge.configure(session_store=...), le retourne.
    Sinon retourne le MemorySessionStore par défaut (mono-processus).
    """
    return _configured_store if _configured_store is not None else _default_store


def set_session_store(store: SessionStore | None) -> None:
    """Injecte le backend de session actif.

    Appelé par forge.configure(session_store=...).
    Passer None réinitialise au MemorySessionStore par défaut.
    """
    global _configured_store
    _configured_store = store
