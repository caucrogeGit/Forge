from contextlib import contextmanager

from core.database.connection import get_connection, close_connection


class Transaction:
    """Transaction explicite autour d'une connexion MariaDB."""

    def __init__(self, connection):
        self.connection = connection

    def cursor(self, *, dictionary=False):
        return self.connection.cursor(dictionary=dictionary)


@contextmanager
def transaction():
    """
    Ouvre une transaction explicite.

    Le développeur choisit le périmètre du bloc. Les helpers DB qui reçoivent
    tx réutilisent la connexion et ne commit jamais eux-mêmes.
    """
    connection = get_connection()
    tx = Transaction(connection)
    try:
        yield tx
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        close_connection(connection)
