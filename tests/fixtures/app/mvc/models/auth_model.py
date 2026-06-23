from core.database.db import execute, fetch_all, fetch_one


GET_UTILISATEUR_PAR_LOGIN = """
SELECT
    u.UtilisateurId,
    u.Login,
    u.PasswordHash,
    u.Prenom,
    u.Nom,
    u.Email,
    u.Actif
FROM utilisateur u
WHERE u.Login = ?
LIMIT 1
"""

GET_ROLES_UTILISATEUR = """
SELECT ur.RoleId
FROM utilisateur_role ur
WHERE ur.UtilisateurId = ?
ORDER BY ur.RoleId
"""

UPDATE_PASSWORD_HASH = "UPDATE utilisateur SET PasswordHash = ? WHERE UtilisateurId = ?"


def update_password_hash(user_id: int, new_hash: str) -> None:
    """Met à jour uniquement le hash du mot de passe de l'utilisateur."""
    execute(UPDATE_PASSWORD_HASH, (new_hash, user_id))


def get_user_by_login(login: str) -> dict | None:
    utilisateur = fetch_one(GET_UTILISATEUR_PAR_LOGIN, (login,))
    if not utilisateur:
        return None
    roles = fetch_all(GET_ROLES_UTILISATEUR, (utilisateur["UtilisateurId"],))
    utilisateur["roles"] = [row["RoleId"] for row in roles]
    return utilisateur
