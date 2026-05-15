"""Hachage et verification des mots de passe Auth/User."""

from __future__ import annotations

from argon2 import PasswordHasher
from argon2.exceptions import Argon2Error, InvalidHashError, VerificationError, VerifyMismatchError

from core.auth.exceptions import AuthError


_PASSWORD_HASHER = PasswordHasher(
    time_cost=2,
    memory_cost=19456,
    parallelism=1,
)


def _validate_password(password: str) -> None:
    if not isinstance(password, str) or not password:
        raise AuthError("password doit etre une chaine non vide")


def _validate_password_hash(password_hash: str) -> None:
    if not isinstance(password_hash, str) or not password_hash:
        raise AuthError("password_hash doit etre une chaine non vide")


def hash_password(password: str) -> str:
    """Retourne un hash Argon2id pour un mot de passe clair."""
    _validate_password(password)
    return _PASSWORD_HASHER.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verifie un mot de passe clair contre un hash Argon2id."""
    try:
        _validate_password(password)
        _validate_password_hash(password_hash)
        return _PASSWORD_HASHER.verify(password_hash, password)
    except (AuthError, InvalidHashError, VerificationError, VerifyMismatchError, Argon2Error):
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """Indique si un hash devrait etre regenere avec les parametres actuels."""
    try:
        _validate_password_hash(password_hash)
        return bool(_PASSWORD_HASHER.check_needs_rehash(password_hash))
    except (AuthError, InvalidHashError, Argon2Error):
        return False
