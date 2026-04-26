from core.database.connection import close_connection, get_connection


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
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(GET_UTILISATEUR_PAR_LOGIN, (login,))
        utilisateur = cursor.fetchone()
        if not utilisateur:
            return None

        utilisateur["roles"] = []
        return utilisateur
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
