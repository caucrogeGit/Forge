"""Association optionnelle entre utilisateurs Auth/User et roles RBAC.

Ce module ne charge aucune permission et ne modifie pas le moteur RBAC. Il
decrit seulement le lien local user_id <-> role_id.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from typing import Any

from core.auth.exceptions import InvalidAuthUserError


@dataclass(frozen=True, kw_only=True)
class AuthUserRole:
    """Lien stockable entre un utilisateur local et un role RBAC."""

    user_id: int
    role_id: int
    created_at: Any | None = None


def validate_user_role_user_id(user_id: Any) -> None:
    """Valide un identifiant utilisateur local."""
    if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
        raise InvalidAuthUserError("user_id doit etre un entier strictement positif")


def validate_user_role_role_id(role_id: Any) -> None:
    """Valide un identifiant role RBAC."""
    if not isinstance(role_id, int) or isinstance(role_id, bool) or role_id <= 0:
        raise InvalidAuthUserError("role_id doit etre un entier strictement positif")


def user_role_key(user_id: Any, role_id: Any) -> str:
    """Retourne la cle stable user_id:role_id."""
    validate_user_role_user_id(user_id)
    validate_user_role_role_id(role_id)
    return f"{user_id}:{role_id}"


def validate_auth_user_role_contract(data: Any) -> None:
    """Valide le contrat AuthUserRole minimal.

    Accepte un AuthUserRole ou un dict brut. Ne lit aucune base de donnees.
    """
    if isinstance(data, AuthUserRole):
        validate_user_role_user_id(data.user_id)
        validate_user_role_role_id(data.role_id)
        return

    if not isinstance(data, dict):
        raise InvalidAuthUserError(
            "les donnees user/role doivent etre un AuthUserRole ou un dict"
        )

    missing = sorted(k for k in ("user_id", "role_id") if k not in data)
    if missing:
        raise InvalidAuthUserError(
            f"champs obligatoires manquants : {', '.join(missing)}"
        )

    validate_user_role_user_id(data["user_id"])
    validate_user_role_role_id(data["role_id"])


def normalize_auth_user_role(data: Any) -> AuthUserRole:
    """Valide et normalise un dict brut ou AuthUserRole."""
    if isinstance(data, AuthUserRole):
        validate_auth_user_role_contract(data)
        return data

    if not isinstance(data, dict):
        raise InvalidAuthUserError(
            "les donnees user/role doivent etre un AuthUserRole ou un dict"
        )

    validate_auth_user_role_contract(data)

    return AuthUserRole(
        user_id=data["user_id"],
        role_id=data["role_id"],
        created_at=data.get("created_at"),
    )


def create_auth_user_role(
    user_id: int,
    role_id: int,
    *,
    created_at: Any | None = None,
) -> AuthUserRole:
    """Construit une association user/role valide."""
    return normalize_auth_user_role({
        "user_id": user_id,
        "role_id": role_id,
        "created_at": created_at,
    })


def auth_user_role_key(association: Any) -> str:
    """Retourne la cle user_id:role_id d'une association normalisable."""
    association = normalize_auth_user_role(association)
    return user_role_key(association.user_id, association.role_id)


def auth_user_roles_match(left: Any, right: Any) -> bool:
    """Compare deux associations par leur couple logique user_id + role_id."""
    try:
        left_key = auth_user_role_key(left)
        right_key = auth_user_role_key(right)
        return secrets.compare_digest(left_key, right_key)
    except InvalidAuthUserError:
        return False


def is_valid_auth_user_role(association: Any) -> bool:
    """Retourne True si association est un AuthUserRole valide."""
    try:
        validate_auth_user_role_contract(association)
    except InvalidAuthUserError:
        return False
    return isinstance(association, AuthUserRole)
