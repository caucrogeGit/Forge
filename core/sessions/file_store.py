# pyright: strict
"""Backend fichier pour les sessions Forge.

Stocke chaque session dans un fichier JSON sous sessions_dir.
Persiste les sessions entre redémarrages du processus.
Le backend par défaut reste MemorySessionStore.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import threading
import time
from pathlib import Path
from typing import Any, cast

from core.sessions.memory_store import SESSION_TTL

# Filtre strict : exactement 64 hex minuscules — aucun chemin traversal possible.
_SESSION_ID_RE = re.compile(r"^[0-9a-f]{64}$")


class FileSessionStore:
    """Backend de session JSON sur disque.

    Chaque session est stockée dans <sessions_dir>/<session_id>.json.
    Thread-safe (RLock). Ne supporte pas le multi-processus concurrent
    sur le même dossier sans verrou externe.
    """

    def __init__(
        self,
        sessions_dir: Path | str = "storage/sessions",
        ttl: int = SESSION_TTL,
    ) -> None:
        self._dir = Path(sessions_dir).resolve()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._ttl = ttl
        self._lock = threading.RLock()

    # ── helpers ─────────────────────────────────────────────────────────────

    def _valid(self, session_id: str) -> bool:
        return bool(_SESSION_ID_RE.match(session_id))

    def _path(self, session_id: str) -> Path:
        return self._dir / f"{session_id}.json"

    def _load(self, session_id: str) -> dict[str, Any] | None:
        """Lit le fichier de session. Retourne None si absent ou corrompu."""
        path = self._path(session_id)
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
            return None
        return cast("dict[str, Any]", raw) if isinstance(raw, dict) else None

    def _save(self, session_id: str, data: dict[str, Any]) -> None:
        # Écriture atomique : on écrit un fichier temporaire dans le même dossier
        # puis on le renomme (os.replace est atomique). Un crash en cours
        # d'écriture ne corrompt donc jamais le fichier de session existant.
        target = self._path(session_id)
        tmp = target.with_name(f"{target.name}.{secrets.token_hex(4)}.tmp")
        try:
            tmp.write_text(json.dumps(data), encoding="utf-8")
            os.replace(tmp, target)
        except OSError:
            # En cas d'échec, ne pas laisser de fichier temporaire orphelin.
            tmp.unlink(missing_ok=True)
            raise

    # ── public API ──────────────────────────────────────────────────────────

    def create(self, data: dict[str, Any] | None = None) -> str:
        """Crée une session avec la structure Forge standard et retourne son identifiant."""
        session_id = secrets.token_hex(32)
        session = {
            **(data or {}),
            "authenticated": False,
            "user": None,
            "csrf_token": secrets.token_hex(16),
            "expires_at": time.time() + self._ttl,
        }
        with self._lock:
            self._save(session_id, session)
        return session_id

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Retourne les données de session ou None si absente, expirée ou corrompue."""
        if not self._valid(session_id):
            return None
        with self._lock:
            data = self._load(session_id)
            if data is None:
                return None
            if time.time() > data.get("expires_at", data.get("expire_a", 0)):
                self._path(session_id).unlink(missing_ok=True)
                return None
            return data

    def set(self, session_id: str, data: dict[str, Any]) -> None:
        """Met à jour (merge) les données d'une session existante."""
        if not self._valid(session_id):
            return
        with self._lock:
            existing = self._load(session_id)
            if existing is None:
                return
            existing.update(data)
            self._save(session_id, existing)

    def replace(self, session_id: str, data: dict[str, Any]) -> None:
        """Remplace intégralement les données d'une session existante (sans merge).

        Contrairement à set(), les clés absentes de data sont supprimées.
        """
        if not self._valid(session_id):
            return
        with self._lock:
            if self._load(session_id) is None:
                return
            self._save(session_id, data)

    def delete(self, session_id: str) -> None:
        """Supprime la session."""
        if not self._valid(session_id):
            return
        with self._lock:
            self._path(session_id).unlink(missing_ok=True)

    def regenerate(self, session_id: str) -> str:
        """Crée un nouveau session_id en préservant les données — protège contre la fixation."""
        nouveau_id = secrets.token_hex(32)
        with self._lock:
            existing = {}
            if self._valid(session_id):
                existing = self._load(session_id) or {}
                self._path(session_id).unlink(missing_ok=True)
            existing["expires_at"] = time.time() + self._ttl
            self._save(nouveau_id, existing)
        return nouveau_id

    def authenticate(self, session_id: str, user_data: dict[str, Any], ttl_seconds: int) -> str | None:
        """Rotation atomique : invalide l'ancienne session, crée une nouvelle authentifiée."""
        if not self._valid(session_id):
            return None
        nouveau_id = secrets.token_hex(32)
        with self._lock:
            existing = self._load(session_id)
            if existing is None:
                return None
            self._path(session_id).unlink(missing_ok=True)
            new_session = {
                **existing,
                "authenticated": True,
                "user": user_data,
                "csrf_token": secrets.token_hex(16),
                "expires_at": time.time() + ttl_seconds,
            }
            self._save(nouveau_id, new_session)
        return nouveau_id

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        """Repousse l'expiration. Retourne False si la session n'existe pas ou est expirée."""
        if not self._valid(session_id):
            return False
        with self._lock:
            data = self._load(session_id)
            if data is None or time.time() > data.get("expires_at", data.get("expire_a", 0)):
                return False
            data["expires_at"] = time.time() + ttl_seconds
            self._save(session_id, data)
            return True

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        """Stocke un message flash. Retourne False si la session n'existe pas."""
        if not self._valid(session_id):
            return False
        with self._lock:
            data = self._load(session_id)
            if data is None:
                return False
            data["flash"] = {"message": message, "level": level}
            self._save(session_id, data)
            return True

    def get_flash(self, session_id: str) -> dict[str, Any] | None:
        """Lit et supprime atomiquement le message flash. Retourne None si absent."""
        if not self._valid(session_id):
            return None
        with self._lock:
            data = self._load(session_id)
            if data is None:
                return None
            flash = data.pop("flash", None)
            if flash is not None:
                self._save(session_id, data)
            return flash

    def cleanup_expired(self) -> int:
        """Supprime les fichiers de session expirés. Retourne le nombre supprimé."""
        now = time.time()
        count = 0
        with self._lock:
            for path in self._dir.glob("*.json"):
                if not _SESSION_ID_RE.match(path.stem):
                    continue
                try:
                    raw = json.loads(path.read_text(encoding="utf-8"))
                    if isinstance(raw, dict):
                        data = cast("dict[str, Any]", raw)
                        expired = now > data.get("expires_at", data.get("expire_a", 0))
                    else:
                        expired = True
                except (json.JSONDecodeError, OSError, ValueError):
                    expired = True
                if expired:
                    path.unlink(missing_ok=True)
                    count += 1
        return count
