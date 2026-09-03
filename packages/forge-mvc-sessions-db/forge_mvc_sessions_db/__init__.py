# pyright: strict
"""forge-mvc-sessions-db — store de session persistant adossé à la BDD.

Extrait du cœur (ADR-054) : un cœur agnostique ne fournit qu'un store mémoire,
un store fichier et le contrat `SessionStore`. Le store BDD, autrefois
`core.sessions.mariadb_store.MariaDbSessionStore`, vit désormais dans cet opt-in
sous le nom générique `DbSessionStore`, avec un SQL portable (horodatages
Python, pas de `NOW()` propriétaire) dispatché vers le backend BDD actif.
"""
from __future__ import annotations

from forge_mvc_sessions_db.metrics import (
    SessionMetrics,
    active_sessions,
    session_metrics,
)
from forge_mvc_sessions_db.store import DbSessionStore
from forge_mvc_sessions_db.ttl import (
    DEFAULT_TTLS,
    KIND_ANONYMOUS,
    KIND_AUTHENTICATED,
    KIND_REMEMBERED,
    SESSION_KINDS,
    SessionTtlError,
    normalize_kind,
    ttl_for,
)

__all__ = [
    "DbSessionStore",
    # Durée de vie par nature (SESSIONS-TTL-PER-KIND-001)
    "ttl_for",
    "normalize_kind",
    "SESSION_KINDS",
    "DEFAULT_TTLS",
    "KIND_ANONYMOUS",
    "KIND_AUTHENTICATED",
    "KIND_REMEMBERED",
    "SessionTtlError",
    # Compteur de sessions actives (SESSIONS-ACTIVE-METRIC-001)
    "active_sessions",
    "session_metrics",
    "SessionMetrics",
]

__version__ = "1.0.0rc7"
