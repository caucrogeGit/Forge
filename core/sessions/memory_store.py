# pyright: strict
"""Backend mémoire pour les sessions Forge (comportement par défaut)."""

from __future__ import annotations

import secrets
import threading
import time
from typing import Any

SESSION_TTL = 3600  # 1 heure en secondes


class MemorySessionStore:
    """Backend de session mono-processus utilisant un dictionnaire Python.

    Thread-safe via RLock (reentrant : create() peut appeler _cleanup() sans
    deadlock). Les sessions sont perdues au redémarrage du processus.
    """

    def __init__(self, ttl: int = SESSION_TTL) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}
        self._lock = threading.RLock()
        self._ttl = ttl

    def create(self, data: dict[str, Any] | None = None) -> str:
        """Crée une session avec la structure Forge standard et retourne son identifiant."""
        session_id = secrets.token_hex(32)
        with self._lock:
            self._sessions[session_id] = {
                **(data or {}),
                "authenticated": False,
                "user": None,
                "csrf_token": secrets.token_hex(16),
                "expires_at": time.time() + self._ttl,
            }
            self._cleanup()
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Retourne les données de session ou None si absente ou expirée."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            if time.time() > session.get("expires_at", session.get("expire_a", 0)):
                self._sessions.pop(session_id, None)
                return None
            return session

    def set(self, session_id: str, data: dict[str, Any]) -> None:
        """Met à jour (merge) les données d'une session existante."""
        with self._lock:
            if session_id in self._sessions:
                self._sessions[session_id].update(data)

    def replace(self, session_id: str, data: dict[str, Any]) -> None:
        """Remplace intégralement les données d'une session existante (sans merge).

        Contrairement à set(), les clés absentes de data sont supprimées.
        Opère sur le dict interne en place pour préserver les références vivantes.
        Prend un snapshot de data avant de vider, car data peut etre le meme objet
        que le dict interne (get() retourne une reference vivante).
        """
        with self._lock:
            existing = self._sessions.get(session_id)
            if existing is None:
                return
            if time.time() > existing.get("expires_at", existing.get("expire_a", 0)):
                self._sessions.pop(session_id, None)
                return
            snapshot = dict(data)
            existing.clear()
            existing.update(snapshot)

    def delete(self, session_id: str) -> None:
        """Supprime la session."""
        with self._lock:
            self._sessions.pop(session_id, None)

    def regenerate(self, session_id: str) -> str:
        """Crée un nouveau session_id en préservant les données — protège contre la fixation."""
        nouveau_id = secrets.token_hex(32)
        with self._lock:
            ancien = self._sessions.pop(session_id, {})
            self._sessions[nouveau_id] = {
                **ancien,
                "expires_at": time.time() + self._ttl,
            }
        return nouveau_id

    def authenticate(self, session_id: str, user_data: dict[str, Any], ttl_seconds: int) -> str | None:
        """Rotation atomique : invalide l'ancienne session, crée une nouvelle authentifiée."""
        nouveau_id = secrets.token_hex(32)
        with self._lock:
            ancien = self._sessions.pop(session_id, None)
            if ancien is None:
                return None
            self._sessions[nouveau_id] = {
                **ancien,
                "authenticated": True,
                "user": user_data,
                "csrf_token": secrets.token_hex(16),
                "expires_at": time.time() + ttl_seconds,
            }
        return nouveau_id

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        """Repousse l'expiration. Retourne False si la session n'existe pas ou est expirée."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None or time.time() > session.get("expires_at", session.get("expire_a", 0)):
                return False
            session["expires_at"] = time.time() + ttl_seconds
            return True

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        """Stocke un message flash. Retourne False si la session n'existe pas."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return False
            session["flash"] = {"message": message, "level": level}
            return True

    def get_flash(self, session_id: str) -> dict[str, Any] | None:
        """Lit et supprime atomiquement le message flash. Retourne None si absent."""
        with self._lock:
            session = self._sessions.get(session_id)
            if session is None:
                return None
            return session.pop("flash", None)

    def purge_all(self) -> None:
        """Vide toutes les sessions — usage réservé aux tests."""
        with self._lock:
            self._sessions.clear()

    def cleanup_expired(self) -> int:
        """Supprime toutes les sessions expirées. Retourne le nombre supprimé.

        Complète le nettoyage opportuniste déjà en place :

          * `get()` / `replace()` / `touch_expiry()` retirent paresseusement
            chaque session expirée à son accès individuel ;
          * `create()` déclenche en plus un balayage global à chaque nouvelle
            session ;
          * `cleanup_expired()` permet à l'application de déclencher
            explicitement un balayage complet à tout moment (ex. cron
            applicatif, healthcheck, fin de batch).

        Aucun thread, aucun scheduler — l'appel reste explicite et borné
        (alignement avec `FileSessionStore.cleanup_expired()` et
        `DbSessionStore.cleanup_expired()`).
        """
        with self._lock:
            return self._cleanup()

    def _cleanup(self) -> int:
        """Supprime les sessions expirées et retourne le nombre supprimé.

        Doit être appelée avec `_lock` déjà acquis (raison du `RLock` :
        `create()` appelle `_cleanup()` à l'intérieur de son propre verrou).
        """
        now = time.time()
        expired = [sid for sid, s in self._sessions.items() if now > s.get("expires_at", s.get("expire_a", 0))]
        for sid in expired:
            del self._sessions[sid]
        return len(expired)
