# pyright: strict
from collections.abc import Sequence
from typing import Any

from core.database.connection import get_connection, close_connection
from core.database.qualify import raise_qualified
from core.database.transaction import Transaction


def fetch_one(sql: str, params: Sequence[Any] = (), *, tx: "Transaction | None" = None) -> "dict[str, Any] | None":
    """Exécute un SELECT explicite et retourne une ligne."""
    return _run_query(sql, params, tx=tx, dictionary=True, fetch="one")


def fetch_all(sql: str, params: Sequence[Any] = (), *, tx: "Transaction | None" = None) -> "list[dict[str, Any]]":
    """Exécute un SELECT explicite et retourne toutes les lignes."""
    return _run_query(sql, params, tx=tx, dictionary=True, fetch="all")


def execute(sql: str, params: Sequence[Any] = (), *, tx: "Transaction | None" = None) -> int:
    """Exécute une requête explicite et retourne rowcount."""
    return _run_query(sql, params, tx=tx, dictionary=False, fetch=None)


def insert(sql: str, params: Sequence[Any] = (), *, tx: "Transaction | None" = None) -> int:
    """Exécute une insertion explicite et retourne lastrowid."""
    return _run_query(sql, params, tx=tx, dictionary=False, fetch="lastrowid")


def _close_quietly(closeable: Any) -> None:
    """Ferme sans jamais lever : la sortie ne doit rien retenir.

    Sur connexion coupée, la fermeture du curseur peut échouer à son tour. Le
    laisser lever depuis le `finally` remplacerait l'erreur d'origine par la
    sienne **et** sauterait la restitution de la connexion qui suit : elle ne
    repartirait pas au pool et son jeton de file d'attente serait perdu,
    réduisant définitivement la capacité (MARIADB-POOL-QUEUE-001).
    """
    try:
        closeable.close()
    except Exception:  # noqa: BLE001 — fermeture best-effort
        pass


def _run_query(sql: str, params: Sequence[Any] = (), *, tx: "Transaction | None" = None,
               dictionary: bool = False, fetch: "str | None" = None) -> Any:
    connection: Any = None
    cursor: Any = None
    owns_connection = tx is None

    try:
        connection = get_connection() if tx is None else tx.connection
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
    except Exception as error:
        if owns_connection and connection is not None:
            # Sur une connexion coupée, le rollback échoue lui aussi : le
            # laisser lever remplacerait l'erreur d'origine par la sienne, et
            # la cause véritable disparaîtrait du rapport.
            try:
                connection.rollback()
            except Exception:  # noqa: BLE001 — annulation best-effort
                pass
        # Deux conditions seulement sont qualifiées (ADR-054) : sans cela une
        # application devrait attraper l'exception de son pilote et ne serait
        # portable sur aucun autre backend. Tout le reste remonte inchangé.
        # Le doublon s'affiche dans un formulaire ; la connexion périmée dans le
        # pool, le serveur redémarré ou basculé font un 503 avec Retry-After,
        # la requête n'ayant rien de fautif et l'emprunt suivant devant réussir.
        raise_qualified(error)
    finally:
        if cursor is not None:
            _close_quietly(cursor)
        if owns_connection:
            close_connection(connection)
