from core.database.connection import close_connection, get_connection


SELECT_VILLES = """
SELECT VilleId, Nom, CodePostal
FROM ville
ORDER BY Nom
"""


def get_villes():
    connection = None
    cursor = None
    try:
        connection = get_connection()
        cursor = connection.cursor(dictionary=True)
        cursor.execute(SELECT_VILLES)
        return cursor.fetchall()
    finally:
        if cursor:
            cursor.close()
        close_connection(connection)
