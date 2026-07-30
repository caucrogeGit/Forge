# pyright: strict
from collections.abc import Generator
from contextlib import contextmanager
from typing import Any

from core.database.connection import get_connection, close_connection
from core.database.qualify import raise_qualified


class Transaction:
    """Transaction explicite autour d'une connexion du backend BDD actif."""

    connection: Any

    def __init__(self, connection: Any) -> None:
        self.connection = connection

    def cursor(self, *, dictionary: bool = False) -> Any:
        return self.connection.cursor(dictionary=dictionary)


def _rollback_quietly(connection: Any) -> None:
    """Annule sans jamais lever : sur connexion coupée, le rollback échoue aussi.

    Le laisser lever remplacerait l'erreur d'origine par la sienne, et la cause
    véritable disparaîtrait du rapport : on diagnostiquerait « connexion morte
    pendant l'annulation » au lieu de la vraie faute, doublon compris. Mesuré,
    c'est exactement ce qui se passait ici alors que `core.database.db` s'en
    protégeait déjà (CORE-TX-LOST-CONNECTION-001).
    """
    try:
        connection.rollback()
    except Exception:  # noqa: BLE001 — annulation best-effort
        pass


def _restore_quietly(connection: Any, autocommit: Any) -> None:
    """Restaure l'autocommit sans lever : la connexion doit être rendue.

    Sur connexion morte, le pilote peut refuser le réglage. Laisser cette
    erreur sortir du `finally` empêcherait la restitution qui suit : la
    connexion ne repartirait pas au pool et son jeton de file d'attente serait
    perdu, réduisant définitivement la capacité (MARIADB-POOL-QUEUE-001).
    """
    try:
        connection.autocommit = autocommit
    except Exception:  # noqa: BLE001 — restitution best-effort
        pass


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

    Ce que le bloc laisse sortir est **toujours** une exception que
    l'application peut nommer sans connaître le pilote (ADR-054) : l'annulation
    ne masque plus la cause, et l'échec de la validation est qualifié comme le
    serait celui d'une requête. La connexion est rendue quoi qu'il arrive, y
    compris quand elle est morte : aucune sortie ne doit retenir un jeton du
    pool.
    """
    connection = get_connection()
    try:
        # L'armement fait partie du bloc protégé : le pool peut livrer une
        # connexion que le serveur a fermée de son côté, et le pilote refuse
        # alors le réglage d'autocommit. Cet échec doit être qualifié comme les
        # autres, et surtout ne pas emporter la connexion avec lui.
        try:
            previous_autocommit = connection.autocommit
            connection.autocommit = False
        except Exception as error:
            raise_qualified(error)

        try:
            yield Transaction(connection)
        except Exception as error:
            _rollback_quietly(connection)
            raise_qualified(error)
        else:
            try:
                connection.commit()
            except Exception as error:
                raise_qualified(error)
        finally:
            _restore_quietly(connection, previous_autocommit)
    finally:
        close_connection(connection)
