from core.database.connection import get_connection, close_connection


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


def get_user_by_login(login: str) -> dict | None:
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(GET_UTILISATEUR_PAR_LOGIN, (login,))
        utilisateur = cursor.fetchone()
        if not utilisateur:
            return None

        cursor.execute(GET_ROLES_UTILISATEUR, (utilisateur["UtilisateurId"],))
        utilisateur["roles"] = [row["RoleId"] for row in cursor.fetchall()]
        return utilisateur
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
