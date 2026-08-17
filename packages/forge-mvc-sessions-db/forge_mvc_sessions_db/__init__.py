# pyright: strict
"""forge-mvc-sessions-db — store de session persistant adossé à la BDD.

Extrait du cœur (ADR-054) : un cœur agnostique ne fournit qu'un store mémoire,
un store fichier et le contrat `SessionStore`. Le store BDD, autrefois
`core.sessions.mariadb_store.MariaDbSessionStore`, vit désormais dans cet opt-in
sous le nom générique `DbSessionStore`, avec un SQL portable (horodatages
Python, pas de `NOW()` propriétaire) dispatché vers le backend BDD actif.
"""
from __future__ import annotations

from forge_mvc_sessions_db.store import DbSessionStore

__all__ = ["DbSessionStore"]

__version__ = "1.0.0rc7"
