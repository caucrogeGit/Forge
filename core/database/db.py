from core.database.connection import get_connection, close_connection


def fetch_one(sql: str, params=(), *, tx=None):
    """Exécute un SELECT explicite et retourne une ligne."""
    return _run_query(sql, params, tx=tx, dictionary=True, fetch="one")


def fetch_all(sql: str, params=(), *, tx=None):
    """Exécute un SELECT explicite et retourne toutes les lignes."""
    return _run_query(sql, params, tx=tx, dictionary=True, fetch="all")


def execute(sql: str, params=(), *, tx=None):
    """Exécute une requête explicite et retourne rowcount."""
    return _run_query(sql, params, tx=tx, dictionary=False, fetch=None)


def insert(sql: str, params=(), *, tx=None):
    """Exécute une insertion explicite et retourne lastrowid."""
    return _run_query(sql, params, tx=tx, dictionary=False, fetch="lastrowid")


def _run_query(sql: str, params=(), *, tx=None, dictionary=False, fetch=None):
    connection = None
    cursor = None
    owns_connection = tx is None

    try:
        connection = get_connection() if owns_connection else tx.connection
        cursor = connection.cursor(dictionary=dictionary)
        cursor.execute(sql, params)

        if fetch == "one":
            result = cursor.fetchone()
        elif fetch == "all":
            result = cursor.fetchall()
        elif fetch == "lastrowid":
            result = cursor.lastrowid
        else:
            result = cursor.rowcount

        # Commit aussi après un SELECT : sans cela, la connexion retourne au
        # pool avec une transaction REPEATABLE READ ouverte, et l'emprunteur
        # suivant hérite d'un snapshot figé (lectures périmées en concurrence).
        if owns_connection:
            connection.commit()
        return result
    except Exception:
        if owns_connection and connection is not None:
            connection.rollback()
        raise
    finally:
        if cursor is not None:
            cursor.close()
        if owns_connection:
            close_connection(connection)
