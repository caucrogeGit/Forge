"""Verification d'adresse email pour Auth/User."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from core.auth.exceptions import AuthError
from core.auth.tokens import (
    AuthToken,
    normalize_auth_token,
    generate_auth_token,
    hash_auth_token,
    is_token_usable,
    token_expires_at,
    verify_auth_token,
)


EMAIL_VERIFICATION_PURPOSE = "email_verification"


def create_email_verification_token(
    user_id: int,
    minutes: int = 60,
    now: datetime | None = None,
) -> tuple[str, AuthToken]:
    """Cree un jeton de verification email.

    Retourne le couple (token_brut, AuthToken).
    Le token brut est transmis une seule fois a l'application pour construire
    un lien de verification. Seul token_hash doit etre stocke cote serveur.
    """
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise AuthError("user_id doit etre un entier strictement positif")

    if not isinstance(minutes, int) or isinstance(minutes, bool) or minutes <= 0:
        raise AuthError("minutes doit etre un entier strictement positif")

    base = now if now is not None else datetime.now(tz=timezone.utc)
    raw_token = generate_auth_token()
    token_hash = hash_auth_token(raw_token)
    expires_at = token_expires_at(minutes, now=base)

    auth_token = AuthToken(
        user_id=user_id,
        purpose=EMAIL_VERIFICATION_PURPOSE,
        token_hash=token_hash,
        expires_at=expires_at,
        used_at=None,
        created_at=base,
    )

    return raw_token, auth_token


def verify_email_verification_token(
    token: str,
    token_record: Any,
    now: datetime | None = None,
) -> bool:
    """Retourne True si le token brut est valide pour la verification email.

    Verifie que le token_record est utilisable, que le purpose est correct et
    que le token brut correspond au token_hash. Ne modifie ni la base ni le
    token_record.
    """
    try:
        if not isinstance(token, str) or not token:
            return False

        if isinstance(token_record, dict):
            token_record = normalize_auth_token(token_record)

        if not isinstance(token_record, AuthToken):
            return False

        if not is_token_usable(token_record, purpose=EMAIL_VERIFICATION_PURPOSE, now=now):
            return False

        return verify_auth_token(token, token_record.token_hash)

    except Exception:
        return False


def email_verification_timestamp(now: datetime | None = None) -> datetime:
    """Retourne la datetime courante en UTC pour renseigner email_verified_at."""
    return now if now is not None else datetime.now(tz=timezone.utc)


def is_email_verified(email_verified_at: Any) -> bool:
    """Retourne True si email_verified_at est renseigne."""
    return email_verified_at is not None
