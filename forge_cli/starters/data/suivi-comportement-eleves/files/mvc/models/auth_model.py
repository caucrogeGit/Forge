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


def get_user_by_login(login: str) -> dict | None:
    """Retourne l'utilisateur par login, sans dépendre de tables de rôles."""
    utilisateur = fetch_one(GET_UTILISATEUR_PAR_LOGIN, (login,))
    if not utilisateur:
        return None
    utilisateur["roles"] = []
    return utilisateur
