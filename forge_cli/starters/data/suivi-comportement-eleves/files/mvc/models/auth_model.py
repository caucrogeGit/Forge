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
    """Retourne l'utilisateur par login, sans dépendre de tables de rôles."""
    utilisateur = fetch_one(GET_UTILISATEUR_PAR_LOGIN, (login,))
    if not utilisateur:
        return None
    utilisateur["roles"] = []
    return utilisateur


def get_user_by_id(user_id: int) -> dict | None:
    """Retourne un dict normalisé pour l'affichage (clés minuscules)."""
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
    email = utilisateur.get("Email") or utilisateur.get("Login") or ""
    return normalize_auth_user({
        "id": utilisateur["UtilisateurId"],
        "email": email,
        "password_hash": utilisateur["PasswordHash"],
        "is_active": bool(utilisateur.get("Actif", True)),
    })
