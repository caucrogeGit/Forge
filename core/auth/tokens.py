# pyright: strict
"""Jetons Auth generiques a usage limite pour Forge."""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, cast

from core.auth.exceptions import AuthError


class InvalidAuthTokenError(AuthError):
    """Donnees de jeton incompletes ou invalides."""


@dataclass(frozen=True)
class AuthToken:
    """Representation Python minimale d'un jeton Auth stockable cote serveur."""

    user_id: int
    purpose: str
    token_hash: str
    expires_at: datetime
    used_at: datetime | None = None
    created_at: datetime | None = None


# ---------------------------------------------------------------------------
# Generation et hachage
# ---------------------------------------------------------------------------


def generate_auth_token(nbytes: int = 32) -> str:
    """Genere un token URL-safe cryptographiquement sur."""
    if not isinstance(nbytes, int) or isinstance(nbytes, bool) or nbytes <= 0:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("nbytes doit etre un entier strictement positif")
    return secrets.token_urlsafe(nbytes)


def hash_auth_token(token: str) -> str:
    """Retourne le SHA-256 hexadecimal du token brut."""
    if not isinstance(token, str) or not token:  # pyright: ignore[reportUnnecessaryIsInstance]
        raise ValueError("token doit etre une chaine non vide")
    return hashlib.sha256(token.encode()).hexdigest()


def verify_auth_token(token: str, token_hash: str) -> bool:
    """Retourne True si le token brut correspond au hash stocke."""
    try:
        if not isinstance(token, str) or not token:  # pyright: ignore[reportUnnecessaryIsInstance]
            return False
        if not isinstance(token_hash, str) or not token_hash:  # pyright: ignore[reportUnnecessaryIsInstance]
            return False
        expected = hash_auth_token(token)
        return secrets.compare_digest(expected, token_hash)
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Expiration
# ---------------------------------------------------------------------------


def token_expires_at(minutes: int = 60, now: datetime | None = None) -> datetime:
    """Retourne la datetime d'expiration a partir de maintenant + minutes."""
    from datetime import timedelta

    base = now if now is not None else datetime.now(tz=timezone.utc)
    return base + timedelta(minutes=minutes)


def is_token_expired(expires_at: datetime, now: datetime | None = None) -> bool:
    """Retourne True si expires_at est dans le passe."""
    base = now if now is not None else datetime.now(tz=timezone.utc)

    # Normalise en naive UTC pour comparaison si les deux sont naives ou tz-aware
    if expires_at.tzinfo is None and base.tzinfo is not None:
        base = base.replace(tzinfo=None)
    elif expires_at.tzinfo is not None and base.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=None)

    return base >= expires_at


# ---------------------------------------------------------------------------
# Usabilite
# ---------------------------------------------------------------------------


def is_token_usable(
    token_record: Any,
    purpose: str | None = None,
    now: datetime | None = None,
) -> bool:
    """Retourne True si le jeton est valide, non expire, non utilise et de bon purpose.

    Accepte un AuthToken ou un dict normalisable.
    """
    try:
        if isinstance(token_record, dict):
            token_record = normalize_auth_token(token_record)

        if not isinstance(token_record, AuthToken):
            return False

        if is_token_expired(token_record.expires_at, now=now):
            return False

        if token_record.used_at is not None:
            return False

        if purpose is not None and token_record.purpose != purpose:
            return False

        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Normalisation et validation
# ---------------------------------------------------------------------------


def _validate_token_fields(
    user_id: Any,
    purpose: Any,
    token_hash: Any,
    expires_at: Any,
) -> None:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidAuthTokenError("user_id doit etre un entier strictement positif")

    if not isinstance(purpose, str) or not purpose.strip():
        raise InvalidAuthTokenError("purpose doit etre une chaine non vide")

    if not isinstance(token_hash, str) or not token_hash:
        raise InvalidAuthTokenError("token_hash doit etre une chaine non vide")

    if not isinstance(expires_at, datetime):
        raise InvalidAuthTokenError("expires_at doit etre une datetime")


def validate_auth_token_contract(data: Any) -> None:
    """Valide le contrat AuthToken minimal."""
    if isinstance(data, AuthToken):
        _validate_token_fields(data.user_id, data.purpose, data.token_hash, data.expires_at)
        return

    if not isinstance(data, dict):
        raise InvalidAuthTokenError("les donnees de jeton doivent etre un AuthToken ou un dict")

    missing = sorted(k for k in ("user_id", "purpose", "token_hash", "expires_at") if k not in data)
    if missing:
        raise InvalidAuthTokenError(f"champs obligatoires manquants : {', '.join(missing)}")

    _validate_token_fields(data["user_id"], data["purpose"], data["token_hash"], data["expires_at"])


def normalize_auth_token(data: Any) -> AuthToken:
    """Valide et normalise un dict brut en AuthToken."""
    if not isinstance(data, dict):
        raise InvalidAuthTokenError("les donnees de jeton doivent etre un dict")

    validate_auth_token_contract(data)

    data = cast("dict[str, Any]", data)
    return AuthToken(
        user_id=data["user_id"],
        purpose=data["purpose"].strip(),
        token_hash=data["token_hash"],
        expires_at=data["expires_at"],
        used_at=data.get("used_at"),
        created_at=data.get("created_at"),
    )


def is_valid_auth_token(token_record: Any) -> bool:
    """Retourne True si token_record est un AuthToken structurellement valide."""
    try:
        validate_auth_token_contract(token_record)
    except InvalidAuthTokenError:
        return False
    return isinstance(token_record, AuthToken)
