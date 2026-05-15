"""Backend MariaDB pour les sessions Forge.

Stocke les sessions dans la table forge_sessions.
Permet le partage de sessions entre processus Forge via une base commune.
Le backend par défaut reste MemorySessionStore.

Table requise : voir mvc/models/sql/forge_sessions.sql.
"""

from __future__ import annotations

import json
import re
import secrets
import time
from datetime import datetime
from typing import Callable

from core.sessions.memory_store import SESSION_TTL

_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")

# ── Requêtes SQL ──────────────────────────────────────────────────────────────

_SQL_INSERT = (
    "INSERT INTO forge_sessions (session_id, data, expire_at, created_at, updated_at)"
    " VALUES (?, ?, ?, NOW(), NOW())"
)
_SQL_SELECT = (
    "SELECT data FROM forge_sessions WHERE session_id = ? AND expire_at > NOW()"
)
_SQL_UPDATE = (
    "UPDATE forge_sessions SET data = ?, updated_at = NOW() WHERE session_id = ?"
)
_SQL_UPDATE_EXPIRY = (
    "UPDATE forge_sessions SET data = ?, expire_at = ?, updated_at = NOW() WHERE session_id = ?"
)
_SQL_DELETE = "DELETE FROM forge_sessions WHERE session_id = ?"
_SQL_CLEANUP = "DELETE FROM forge_sessions WHERE expire_at < NOW()"


# ── Accesseurs DB par défaut (lazy — pas de connexion à l'import) ─────────────

def _default_fetch_one(sql: str, params: tuple) -> dict | None:
    from core.database.db import fetch_one
    return fetch_one(sql, params)


def _default_execute(sql: str, params: tuple = ()) -> int:
    from core.database.db import execute
    return execute(sql, params)


def _dt(unix_ts: float) -> str:
    """Convertit un timestamp Unix en DATETIME MariaDB (heure locale)."""
    return datetime.fromtimestamp(unix_ts).strftime("%Y-%m-%d %H:%M:%S")


# ── Store ─────────────────────────────────────────────────────────────────────

class MariaDbSessionStore:
    """Backend de session utilisant la table MariaDB forge_sessions.

    Sessions partagées entre processus Forge. Persiste les sessions après
    redémarrage. Ne devient pas le backend par défaut.

    Les callables fetch_one et execute sont injectables pour les tests.
    """

    def __init__(
        self,
        fetch_one: Callable | None = None,
        execute: Callable | None = None,
        ttl: int = SESSION_TTL,
    ) -> None:
        self._fetch_one = fetch_one or _default_fetch_one
        self._execute = execute or _default_execute
        self._ttl = ttl

    # ── helpers ─────────────────────────────────────────────────────────────

    def _valid(self, session_id: str) -> bool:
        return bool(_SESSION_ID_RE.match(session_id))

    def _load(self, session_id: str) -> dict | None:
        """Charge et désérialise une session non expirée. Retourne None si absente,
        expirée ou corrompue."""
        row = self._fetch_one(_SQL_SELECT, (session_id,))
        if not row:
            return None
        try:
            data = json.loads(row["data"])
        except (json.JSONDecodeError, TypeError, ValueError, KeyError):
            self._execute(_SQL_DELETE, (session_id,))
            return None
        return data if isinstance(data, dict) else None

    # ── API publique ─────────────────────────────────────────────────────────

    def create(self, data: dict | None = None) -> str:
        """Crée une session avec la structure Forge standard et retourne son identifiant."""
        session_id = secrets.token_hex(32)
        expires_at = time.time() + self._ttl
        session = {
            **(data or {}),
            "authenticated": False,
            "user": None,
            "csrf_token": secrets.token_hex(16),
            "expires_at": expires_at,
        }
        self._execute(_SQL_INSERT, (session_id, json.dumps(session), _dt(expires_at)))
        return session_id

    def get(self, session_id: str) -> dict | None:
        """Retourne les données de session ou None si absente, expirée ou corrompue."""
        if not self._valid(session_id):
            return None
        return self._load(session_id)

    def set(self, session_id: str, data: dict) -> None:
        """Met à jour (merge) les données d'une session existante non expirée."""
        if not self._valid(session_id):
            return
        existing = self._load(session_id)
        if existing is None:
            return
        existing.update(data)
        self._execute(_SQL_UPDATE, (json.dumps(existing), session_id))

    def replace(self, session_id: str, data: dict) -> None:
        """Remplace intégralement les données d'une session existante (sans merge).

        Contrairement à set(), les clés absentes de data sont supprimées.
        """
        if not self._valid(session_id):
            return
        if self._load(session_id) is None:
            return
        self._execute(_SQL_UPDATE, (json.dumps(data), session_id))

    def delete(self, session_id: str) -> None:
        """Supprime la session."""
        if not self._valid(session_id):
            return
        self._execute(_SQL_DELETE, (session_id,))

    def regenerate(self, session_id: str) -> str:
        """Crée un nouveau session_id en préservant les données — protège contre la fixation."""
        existing = {}
        if self._valid(session_id):
            existing = self._load(session_id) or {}
            self._execute(_SQL_DELETE, (session_id,))
        nouveau_id = secrets.token_hex(32)
        expires_at = time.time() + self._ttl
        existing["expires_at"] = expires_at
        self._execute(_SQL_INSERT, (nouveau_id, json.dumps(existing), _dt(expires_at)))
        return nouveau_id

    def authenticate(self, session_id: str, user_data: dict, ttl_seconds: int) -> str | None:
        """Rotation atomique : invalide l'ancienne session, crée une nouvelle authentifiée."""
        if not self._valid(session_id):
            return None
        existing = self._load(session_id)
        if existing is None:
            return None
        self._execute(_SQL_DELETE, (session_id,))
        nouveau_id = secrets.token_hex(32)
        expires_at = time.time() + ttl_seconds
        new_session = {
            **existing,
            "authenticated": True,
            "user": user_data,
            "csrf_token": secrets.token_hex(16),
            "expires_at": expires_at,
        }
        self._execute(_SQL_INSERT, (nouveau_id, json.dumps(new_session), _dt(expires_at)))
        return nouveau_id

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        """Repousse l'expiration. Retourne False si la session n'existe pas ou est expirée."""
        if not self._valid(session_id):
            return False
        data = self._load(session_id)
        if data is None:
            return False
        expires_at = time.time() + ttl_seconds
        data["expires_at"] = expires_at
        self._execute(_SQL_UPDATE_EXPIRY, (json.dumps(data), _dt(expires_at), session_id))
        return True

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        """Stocke un message flash. Retourne False si la session n'existe pas."""
        if not self._valid(session_id):
            return False
        data = self._load(session_id)
        if data is None:
            return False
        data["flash"] = {"message": message, "level": level}
        self._execute(_SQL_UPDATE, (json.dumps(data), session_id))
        return True

    def get_flash(self, session_id: str) -> dict | None:
        """Lit et supprime atomiquement le message flash. Retourne None si absent."""
        if not self._valid(session_id):
            return None
        data = self._load(session_id)
        if data is None:
            return None
        flash = data.pop("flash", None)
        if flash is not None:
            self._execute(_SQL_UPDATE, (json.dumps(data), session_id))
        return flash

    def cleanup_expired(self) -> int:
        """Supprime les sessions expirées. Retourne le nombre de lignes supprimées."""
        return self._execute(_SQL_CLEANUP, ()) or 0
