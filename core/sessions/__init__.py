# pyright: strict
"""Backends de session Forge.

Le backend par défaut est MemorySessionStore (mono-processus). Le cœur fournit
aussi FileSessionStore et le contrat SessionStore. Le store adossé à la BDD a
été extrait vers l'opt-in forge-mvc-sessions-db (DbSessionStore, ADR-054) : un
cœur agnostique du SGBD n'embarque pas de store BDD.
"""

from core.sessions.contract import SessionStore
from core.sessions.file_store import FileSessionStore
from core.sessions.manager import get_session_store, set_session_store
from core.sessions.memory_store import MemorySessionStore, SESSION_TTL

__all__ = [
    "SessionStore",
    "MemorySessionStore",
    "FileSessionStore",
    "SESSION_TTL",
    "get_session_store",
    "set_session_store",
]
