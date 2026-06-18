# pyright: strict
"""Accès base de données pour les facteurs MFA de l'application MVC."""
from __future__ import annotations

from typing import Any

from forge_mvc_mfa.mfa import MFA_STATUS_ACTIVE, AuthMfaFactor
from core.database.db import fetch_all, fetch_one

_GET_ACTIVE_MFA_FACTORS_SQL = (
    "SELECT id, user_id, factor_type, totp_secret, status, label,"
    " confirmed_at, last_used_at, created_at, updated_at"
    " FROM auth_mfa_factors"
    " WHERE user_id = ? AND status = ?"
)

_GET_USER_BY_ID_SQL = (
    "SELECT UtilisateurId, Login, PasswordHash, Prenom, Nom, Email, Actif"
    " FROM utilisateur"
    " WHERE UtilisateurId = ?"
    " LIMIT 1"
)

_GET_ROLES_BY_USER_ID_SQL = (
    "SELECT RoleId FROM utilisateur_role WHERE UtilisateurId = ? ORDER BY RoleId"
)


def get_active_mfa_factors(user_id: int) -> list[AuthMfaFactor]:
    """Retourne les facteurs MFA actifs pour un utilisateur. Retourne [] en cas d'erreur."""
    try:
        rows = fetch_all(_GET_ACTIVE_MFA_FACTORS_SQL, (user_id, MFA_STATUS_ACTIVE))
        factors: list[AuthMfaFactor] = []
        for row in rows:
            try:
                factors.append(AuthMfaFactor(
                    id=row["id"],
                    user_id=row["user_id"],
                    factor_type=row["factor_type"],
                    totp_secret=row["totp_secret"],
                    status=row["status"],
                    label=row.get("label"),
                    confirmed_at=row.get("confirmed_at"),
                    last_used_at=row.get("last_used_at"),
                    created_at=row.get("created_at"),
                    updated_at=row.get("updated_at"),
                ))
            except Exception:
                continue
        return factors
    except Exception:
        return []


def get_user_by_id(user_id: int) -> dict[str, Any] | None:
    """Retourne le dict utilisateur (utilisateur) par UtilisateurId."""
    utilisateur = fetch_one(_GET_USER_BY_ID_SQL, (user_id,))
    if not utilisateur:
        return None
    roles = fetch_all(_GET_ROLES_BY_USER_ID_SQL, (user_id,))
    utilisateur["roles"] = [row["RoleId"] for row in roles]
    return utilisateur
