# pyright: strict
"""Contrat utilisateur minimal Forge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, cast

from core.auth.exceptions import InvalidAuthUserError


@dataclass(frozen=True)
class AuthUser:
    """Representation Python minimale d'un utilisateur authentifiable."""

    id: int
    email: str
    password_hash: str
    is_active: bool = True
    created_at: Any | None = None
    updated_at: Any | None = None


def _validate_fields(
    user_id: Any,
    email: Any,
    password_hash: Any,
    is_active: Any,
) -> None:
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidAuthUserError("id doit etre un entier strictement positif")

    if not isinstance(email, str) or not email.strip():
        raise InvalidAuthUserError("email doit etre une chaine non vide")

    if not isinstance(password_hash, str) or not password_hash:
        raise InvalidAuthUserError("password_hash doit etre une chaine non vide")

    if not isinstance(is_active, bool):
        raise InvalidAuthUserError("is_active doit etre un booleen")


def validate_auth_user_contract(data: Any) -> None:
    """Valide le contrat AuthUser minimal.

    Accepte un AuthUser deja construit ou un dict brut contenant les champs
    minimaux. Le helper ne cree aucune session et ne lit aucune base de donnees.
    """
    if isinstance(data, AuthUser):
        _validate_fields(data.id, data.email, data.password_hash, data.is_active)
        return

    if not isinstance(data, dict):
        raise InvalidAuthUserError("les donnees utilisateur doivent etre un AuthUser ou un dict")

    missing = sorted(k for k in ("id", "email", "password_hash") if k not in data)
    if missing:
        raise InvalidAuthUserError(f"champs obligatoires manquants : {', '.join(missing)}")

    data = cast("dict[str, Any]", data)
    _validate_fields(
        data["id"],
        data["email"],
        data["password_hash"],
        data.get("is_active", True),
    )


def normalize_auth_user(data: Any) -> AuthUser:
    """Valide et normalise un dict brut en AuthUser.

    Le helper leve InvalidAuthUserError si les donnees sont incompletes ou
    invalides.
    """
    if not isinstance(data, dict):
        raise InvalidAuthUserError("les donnees utilisateur doivent etre un dict")

    validate_auth_user_contract(data)

    data = cast("dict[str, Any]", data)
    return AuthUser(
        id=data["id"],
        email=data["email"].strip(),
        password_hash=data["password_hash"],
        is_active=data.get("is_active", True),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
    )


def is_valid_auth_user(user: Any) -> bool:
    """Retourne True si user est un AuthUser structurellement valide."""
    try:
        validate_auth_user_contract(user)
    except InvalidAuthUserError:
        return False
    return isinstance(user, AuthUser)
