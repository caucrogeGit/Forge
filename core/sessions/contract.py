# pyright: strict
"""Contrat de backend de session Forge."""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class SessionStore(Protocol):
    """Interface complète pour tout backend de session Forge.

    Implémentations disponibles :
    - MemorySessionStore (défaut, mono-processus)
    - FileSessionStore (persistance JSON sur disque)
    - MariaDbSessionStore (sessions partagées entre processus)
    """

    def create(self, data: dict[str, Any] | None = None) -> str:
        """Crée une nouvelle session et retourne son identifiant."""
        ...

    def get(self, session_id: str) -> dict[str, Any] | None:
        """Retourne les données de la session ou None si absente/expirée."""
        ...

    def set(self, session_id: str, data: dict[str, Any]) -> None:
        """Met à jour (merge) les données d'une session existante."""
        ...

    def replace(self, session_id: str, data: dict[str, Any]) -> None:
        """Remplace intégralement les données d'une session existante (sans merge)."""
        ...

    def delete(self, session_id: str) -> None:
        """Supprime la session."""
        ...

    def regenerate(self, session_id: str) -> str:
        """Crée un nouveau session_id en conservant les données existantes."""
        ...

    def authenticate(self, session_id: str, user_data: dict[str, Any], ttl_seconds: int) -> str | None:
        """Authentifie atomiquement : rotation de session_id + écriture utilisateur + nouveau CSRF.

        Retourne le nouveau session_id, ou None si la session n'existe pas.
        """
        ...

    def touch_expiry(self, session_id: str, ttl_seconds: int) -> bool:
        """Repousse l'expiration de la session. Retourne False si la session n'existe pas."""
        ...

    def set_flash(self, session_id: str, message: str, level: str = "success") -> bool:
        """Stocke un message flash. Retourne False si la session n'existe pas."""
        ...

    def get_flash(self, session_id: str) -> dict[str, Any] | None:
        """Lit et supprime atomiquement le message flash. Retourne None si absent."""
        ...
