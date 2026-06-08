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

# Borne haute de longueur de mot de passe (SEC-AUTH-PASSWORD-MAXLEN-001).
# Argon2 pre-hache l'entree entiere (cout lineaire en longueur) avant la partie
# memoire-dure : sans plafond, un mot de passe de plusieurs Mo envoye a hash() ou
# verify() (login non authentifie) ouvre un vecteur de deni de service. 128 est
# largement au-dessus de tout mot de passe legitime (OWASP ASVS exige >= 64).
_MAX_PASSWORD_LENGTH = 128


def _validate_password(password: str) -> None:
    if not isinstance(password, str) or not password:
        raise AuthError("password doit etre une chaine non vide")
    if len(password) > _MAX_PASSWORD_LENGTH:
        raise AuthError(
            f"password ne doit pas depasser {_MAX_PASSWORD_LENGTH} caracteres"
        )


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
