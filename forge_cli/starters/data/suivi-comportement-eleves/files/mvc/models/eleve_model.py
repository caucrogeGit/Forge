from core.database.connection import close_connection, get_connection

SELECT_ELEVES = """
SELECT Id, Nom, Prenom, Classe, Actif
FROM eleve
ORDER BY Classe, Nom, Prenom
"""

SELECT_ELEVE_BY_ID = """
SELECT Id, Nom, Prenom, Classe, Actif
FROM eleve
WHERE Id = ?
LIMIT 1
"""


def get_eleves() -> list[dict]:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_ELEVES)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_eleves_actifs() -> list[dict]:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_ELEVES.replace("FROM eleve", "FROM eleve WHERE Actif = 1"))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_eleve_by_id(eleve_id: int) -> dict | None:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_ELEVE_BY_ID, (eleve_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
