from core.auth import AuthUser, normalize_auth_user
from core.database.db import fetch_one


GET_UTILISATEUR_PAR_LOGIN = """
SELECT
    UtilisateurId,
    Login,
    PasswordHash,
    Prenom,
    Nom,
    Email,
    Actif
FROM utilisateur
WHERE Login = ?
LIMIT 1
"""

GET_UTILISATEUR_PAR_ID = """
SELECT
    UtilisateurId,
    Login,
    PasswordHash,
    Prenom,
    Nom,
    Email,
    Actif
FROM utilisateur
WHERE UtilisateurId = ?
LIMIT 1
"""


def get_user_by_login(login: str) -> dict | None:
    """Retourne le dict brut de l'utilisateur par login."""
    return fetch_one(GET_UTILISATEUR_PAR_LOGIN, (login,))


def get_user_by_id(user_id: int) -> dict | None:
    """Retourne un dict normalisé pour l'affichage en session (clés minuscules)."""
    row = fetch_one(GET_UTILISATEUR_PAR_ID, (user_id,))
    if not row:
        return None
    return {
        "id": row["UtilisateurId"],
        "login": row["Login"],
        "prenom": row.get("Prenom") or "",
        "nom": row.get("Nom") or "",
        "email": row.get("Email") or "",
    }


def build_auth_user(utilisateur: dict) -> AuthUser:
    """Convertit un dict DB en AuthUser pour core.auth.login_user."""
    return normalize_auth_user({
        "id": utilisateur["UtilisateurId"],
        "email": utilisateur["Login"],
        "password_hash": utilisateur["PasswordHash"],
        "is_active": bool(utilisateur["Actif"]),
    })
