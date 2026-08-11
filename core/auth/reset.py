# pyright: strict
"""Demande et reinitialisation de mot de passe pour Auth/User."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from core.auth.exceptions import AuthError, InvalidNewPasswordError
from core.auth.tokens import (
    AuthToken,
    generate_auth_token,
    hash_auth_token,
    is_token_usable,
    normalize_auth_token,
    token_expires_at,
    verify_auth_token,
)
from core.auth.user import AuthUser, normalize_auth_user

_MIN_PASSWORD_LENGTH = 8


PASSWORD_RESET_PURPOSE = "password_reset"


@dataclass(frozen=True)
class PasswordResetRequest:
    """Donnees necessaires pour envoyer un lien de reset password.

    raw_token est transmis une seule fois a l'application pour construire le
    lien. token_record contient le hash a stocker en base. Forge ne stocke
    jamais le token brut.
    """

    user_id: int
    #: Contact du compte, ou `None` s'il n'en a pas (ADR-089). Un compte sans
    #: adresse est un compte valide, et il n'est alors pas récupérable par
    #: courriel : l'application qui reçoit `None` ne doit rien envoyer.
    email: str | None
    raw_token: str
    token_record: AuthToken


def create_password_reset_token(
    user_id: int,
    minutes: int = 30,
    now: datetime | None = None,
) -> tuple[str, AuthToken]:
    """Cree un jeton de reinitialisation de mot de passe.

    Retourne le couple (token_brut, AuthToken).
    Le token brut est transmis une seule fois a l'application pour construire
    un lien de reset. Seul token_hash doit etre stocke cote serveur.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise AuthError("user_id doit etre un entier strictement positif")

    if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise AuthError("minutes doit etre un entier strictement positif")

    base = now if now is not None else datetime.now(tz=timezone.utc)
    raw_token = generate_auth_token()
    token_hash = hash_auth_token(raw_token)
    expires_at = token_expires_at(minutes, now=base)

    auth_token = AuthToken(
        user_id=user_id,
        purpose=PASSWORD_RESET_PURPOSE,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=None,
        created_at=base,
    )

    return raw_token, auth_token


def verify_password_reset_token(
    token: str,
    token_record: Any,
    now: datetime | None = None,
) -> bool:
    """Retourne True si le token brut est valide pour le reset password.

    Verifie que le token_record est utilisable, que le purpose est correct et
    que le token brut correspond au token_hash. Ne modifie ni la base ni le
    token_record.
    """
    try:
        if not isinstance(token, str) or not token:  # pyright: ignore[reportUnnecessaryIsInstance]
            return False

        if isinstance(token_record, dict):
            token_record = normalize_auth_token(token_record)

        if not isinstance(token_record, AuthToken):
            return False

        if not is_token_usable(token_record, purpose=PASSWORD_RESET_PURPOSE, now=now):
            return False

        return verify_auth_token(token, token_record.token_hash)

    except Exception:
        return False


def password_reset_timestamp(now: datetime | None = None) -> datetime:
    """Retourne la datetime courante en UTC pour renseigner auth_tokens.used_at."""
    return now if now is not None else datetime.now(tz=timezone.utc)


def create_password_reset_request(
    user: Any,
    minutes: int = 30,
    now: datetime | None = None,
) -> PasswordResetRequest:
    """Cree une demande de reset password a partir d'un utilisateur valide.

    Accepte un AuthUser ou un dict normalisable. Refuse un utilisateur inactif
    ou invalide. Ne modifie ni la base ni le mot de passe.
    """
    if isinstance(user, dict):
        user = normalize_auth_user(user)

    if not isinstance(user, AuthUser):
        raise AuthError("user doit etre un AuthUser ou un dict normalisable")

    if not user.is_active:
        raise AuthError("impossible de creer une demande de reset pour un utilisateur inactif")

    raw_token, token_record = create_password_reset_token(
        user_id=user.id,
        minutes=minutes,
        now=now,
    )

    return PasswordResetRequest(
        user_id=user.id,
        email=user.email,
        raw_token=raw_token,
        token_record=token_record,
    )


# ---------------------------------------------------------------------------
# Reinitialisation effective du mot de passe
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class PasswordResetResult:
    """Resultat de la reinitialisation de mot de passe.

    Contient le nouveau password_hash pret a etre stocke dans users.password_hash
    et le used_at pret a etre stocke dans auth_tokens.used_at. Ne contient ni
    le mot de passe clair ni le token brut.
    """

    user_id: int
    password_hash: str
    used_at: datetime


def validate_new_password(password: str) -> None:
    """Valide le nouveau mot de passe.

    Leve InvalidNewPasswordError si le mot de passe est invalide.
    """
    from core.auth.password import _MAX_PASSWORD_LENGTH  # pyright: ignore[reportPrivateUsage]

    if not isinstance(password, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise InvalidNewPasswordError("le nouveau mot de passe doit etre une chaine")
    if not password:
        raise InvalidNewPasswordError("le nouveau mot de passe ne peut pas etre vide")
    if len(password) < _MIN_PASSWORD_LENGTH:
        raise InvalidNewPasswordError(
            f"le nouveau mot de passe doit contenir au moins {_MIN_PASSWORD_LENGTH} caracteres"
        )
    if len(password) > _MAX_PASSWORD_LENGTH:
        raise InvalidNewPasswordError(
            f"le nouveau mot de passe ne doit pas depasser {_MAX_PASSWORD_LENGTH} caracteres"
        )


def reset_password_with_token(
    token: str,
    token_record: Any,
    new_password: str,
    now: datetime | None = None,
) -> PasswordResetResult | None:
    """Verifie le token de reset et produit un nouveau hash de mot de passe.

    Retourne PasswordResetResult si le token est valide et le mot de passe
    acceptable. Retourne None si le token est invalide, expire, deja utilise ou
    de mauvais purpose.

    Leve InvalidNewPasswordError si le nouveau mot de passe est invalide.

    Ne modifie ni la base, ni token_record, ni users.password_hash directement.
    """
    from core.auth.password import hash_password

    validate_new_password(new_password)

    if not verify_password_reset_token(token, token_record, now=now):
        return None

    if isinstance(token_record, dict):
        token_record = normalize_auth_token(token_record)

    new_hash = hash_password(new_password)
    used_at = password_reset_timestamp(now=now)

    return PasswordResetResult(
        user_id=token_record.user_id,
        password_hash=new_hash,
        used_at=used_at,
    )
