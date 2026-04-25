"""
core/database/connection.py — Pool de connexions MariaDB
=========================================================
Le pool est créé au premier appel de get_connection() (lazy init).
L'import de ce module ne produit aucun effet de bord réseau.

Chaque requête HTTP emprunte une connexion et la restitue automatiquement
à l'appel de connection.close() — la connexion retourne au pool,
elle n'est pas détruite.

Avantages par rapport à une connexion par requête :
    - Pas d'overhead d'ouverture/fermeture à chaque requête
    - Nombre de connexions simultanées contrôlé (pool_size)
    - Thread-safe : le pool gère la concurrence en interne
"""
import logging
import threading
from core.forge import get as _cfg

logger = logging.getLogger(__name__)

_pool      = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                import mariadb as _mariadb
                _pool = _mariadb.ConnectionPool(
                    host      = _cfg("db_host"),
                    port      = _cfg("db_port"),
                    user      = _cfg("db_user"),
                    password  = _cfg("db_password"),
                    database  = _cfg("db_name"),
                    pool_name = _cfg("app_name").lower(),
                    pool_size = _cfg("db_pool_size"),
                )
                logger.debug("Pool MariaDB initialisé (%s, taille=%s)",
                             _cfg("db_name"), _cfg("db_pool_size"))
    return _pool


def get_connection():
    """Emprunte une connexion depuis le pool (créé au premier appel)."""
    import mariadb as _mariadb
    try:
        return _get_pool().get_connection()
    except _mariadb.PoolError as error:
        logger.exception("Pool épuisé ou connexion impossible : %s", error)
        raise


def close_connection(connection) -> None:
    """Restitue la connexion au pool."""
    if connection is not None:
        connection.close()
