# pyright: strict
"""Backends de session Forge.

Le backend par défaut est MemorySessionStore (mono-processus).
Les backends fichier et MariaDB sont prévus dans des tickets séparés.
"""

from core.sessions.contract import SessionStore
from core.sessions.file_store import FileSessionStore
from core.sessions.manager import get_session_store, set_session_store
from core.sessions.mariadb_store import MariaDbSessionStore
from core.sessions.memory_store import MemorySessionStore, SESSION_TTL

__all__ = [
    "SessionStore",
    "MemorySessionStore",
    "FileSessionStore",
    "MariaDbSessionStore",
    "SESSION_TTL",
    "get_session_store",
    "set_session_store",
]
