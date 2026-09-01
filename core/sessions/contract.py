# pyright: strict
"""Contrat de backend de session Forge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


#: Longueur du préfixe montré à l'écran. Assez pour distinguer deux lignes,
#: trop court pour servir de jeton.
HANDLE_LENGTH = 8


def summary_timestamp(value: object) -> "float | None":
    """Horodatage en nombre, ou `None` si la session ne le porte pas.

    Une session créée avant `ADMIN-SESSIONS-VIEW-001` n'a pas de date de
    création : rendre `None` le dit, là où un zéro se lirait comme 1970.
    """
    return float(value) if isinstance(value, (int, float)) else None


@dataclass(frozen=True)
class SessionSummary:
    """Ce qu'un écran peut montrer d'une session, sans rien compromettre.

    `handle` est un préfixe court de l'identifiant, assez pour distinguer deux
    lignes à l'œil, trop court pour servir de jeton. Il ne permet **pas** de
    révoquer : la révocation se fait par compte, ou par la session elle même
    quand son titulaire la connaît déjà par son cookie.

    `created_at` et `expires_at` sont des horodatages Unix, tels que les stores
    les gardent. Ni adresse ni navigateur : Forge ne les enregistre pas, et
    prétendre le contraire dans un écran serait mentir.
    """

    handle: str
    created_at: "float | None" = None
    expires_at: "float | None" = None
    is_current: bool = False


@runtime_checkable
class SessionStore(Protocol):
    """Interface complète pour tout backend de session Forge.

    Implémentations disponibles :
    - MemorySessionStore (défaut, mono-processus)
    - FileSessionStore (persistance JSON sur disque)
    - DbSessionStore (sessions partagées entre processus)
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

    def list_for_user(self, user_id: object) -> "list[SessionSummary]":
        """Résumés des sessions ouvertes de `user_id`, la plus récente d'abord.

        Sert un écran « mes sessions » ou « sessions actives » : sans lui,
        révoquer était possible mais voir ne l'était pas, et l'exploitant
        déconnectait à l'aveugle (`ADMIN-SESSIONS-VIEW-001`).

        Un résumé **ne porte jamais l'identifiant de session**. Cet identifiant
        est le jeton d'authentification lui même : l'afficher donnerait à qui
        lit la page le pouvoir d'usurper la session, et un écran d'administration
        est justement lu par quelqu'un d'autre que son titulaire.
        """
        ...

    def delete_for_user(
        self, user_id: object, *, except_session_id: str | None = None
    ) -> int:
        """Supprime les sessions de `user_id`. Retourne le nombre supprimé.

        Sert à révoquer l'accès d'un compte d'un seul geste : activation d'un
        second facteur, changement de mot de passe, déconnexion à distance.
        Sans cette primitive, une session ouverte survivait à ces événements
        (`SESSIONS-DELETE-FOR-USER-001`).

        `except_session_id` épargne une session, celle depuis laquelle le geste
        est fait. Sans elle, activer un second facteur déconnecterait celui qui
        vient de l'activer, ce qui ne protège de rien
        (`MFA-SESSION-INVALIDATION-001`).

        L'identité est celle posée par `login_user`, sous la clé
        `SESSION_KEY_AUTH_USER_ID`. Une session anonyme n'est jamais touchée.
        """
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
