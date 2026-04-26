from core.database.connection import close_connection, get_connection

SELECT_COURS = """
SELECT Id, DateCours, Titre, Classe
FROM cours
ORDER BY DateCours DESC, Id DESC
"""

SELECT_COURS_BY_ID = """
SELECT Id, DateCours, Titre, Classe
FROM cours
WHERE Id = ?
LIMIT 1
"""

SELECT_COURS_RECENTS = """
SELECT Id, DateCours, Titre, Classe
FROM cours
ORDER BY DateCours DESC, Id DESC
LIMIT ?
"""


def get_cours() -> list[dict]:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_COURS)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_cours_by_id(cours_id: int) -> dict | None:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_COURS_BY_ID, (cours_id,))
        return cursor.fetchone()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)


def get_cours_recents(limit: int = 5) -> list[dict]:
    connection = cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_COURS_RECENTS, (limit,))
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
