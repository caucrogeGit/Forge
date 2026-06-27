# pyright: strict
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from core.database.connection import get_connection, close_connection


class Transaction:
    """Transaction explicite autour d'une connexion du backend BDD actif."""

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

    Le backend peut fournir des connexions en autocommit : sans le désarmer,
    chaque requête serait validée immédiatement et le rollback serait sans
    effet. On garantit donc un vrai contexte transactionnel le temps du bloc,
    puis on restaure l'état initial avant de rendre la connexion au backend.
    """
    connection = get_connection()
    previous_autocommit = connection.autocommit
    connection.autocommit = False
    tx = Transaction(connection)
    try:
        yield tx
    except Exception:
        connection.rollback()
        raise
    else:
        connection.commit()
    finally:
        connection.autocommit = previous_autocommit
        close_connection(connection)
