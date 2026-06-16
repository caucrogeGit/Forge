# pyright: strict
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from core.database.connection import get_connection, close_connection


class Transaction:
    """Transaction explicite autour d'une connexion MariaDB."""

    connection: Any

    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def cursor(self, *, dictionary: bool = False) -> Any:
        return self.connection.cursor(dictionary=dictionary)


@contextmanager
def transaction() -> Generator["Transaction", None, None]:
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
