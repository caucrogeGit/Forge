# pyright: strict
# mariadb ne fournit pas de stubs de types (paquet sans py.typed) : on accepte
# l'absence de stubs pour ce pilote externe et on aliase le module en `Any`
# localement pour ses accès membres (ConnectionPool, PoolError).
# pyright: reportMissingTypeStubs=false
"""
core/database/connection.py — Pool de connexions MariaDB (API interne)
=======================================================================
Ce module est une API interne. Pour le code applicatif, utiliser plutôt
`core.database.db` qui fournit `fetch_one`, `fetch_all`, `execute`, `insert`.

Les fonctions de ce module sont à utiliser uniquement pour :
- transactions multi-statement (via `core.database.transaction`)
- opérations en bulk avec optimisations spécifiques
- scripts d'administration

Pour tout le reste, utiliser `core.database.db`.

---

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
from typing import Any

from core.forge import get as _cfg

logger = logging.getLogger(__name__)

_pool:      Any = None
_pool_lock = threading.Lock()


def _get_pool() -> Any:
    global _pool
    if _pool is None:
        with _pool_lock:
            if _pool is None:
                import mariadb
                _mariadb: Any = mariadb
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


def get_connection() -> Any:
    """Emprunte une connexion depuis le pool (créé au premier appel)."""
    import mariadb
    _mariadb: Any = mariadb
    try:
        return _get_pool().get_connection()
    except _mariadb.PoolError as error:
        logger.exception("Pool épuisé ou connexion impossible : %s", error)
        raise


def close_connection(connection: Any) -> None:
    """Restitue la connexion au pool."""
    if connection is not None:
        connection.close()
