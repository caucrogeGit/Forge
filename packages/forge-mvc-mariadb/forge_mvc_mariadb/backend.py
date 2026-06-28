# pyright: strict
# mariadb ne fournit pas de stubs de types (paquet sans py.typed) : on accepte
# l'absence de stubs pour ce pilote externe et on aliase le module en `Any`
# localement pour ses accès membres (ConnectionPool, PoolError).
# pyright: reportMissingTypeStubs=false
"""
forge_mvc_mariadb.backend — Backend BDD MariaDB pour Forge (ADR-054)
====================================================================
Implémente le contrat `core.database.backend.DatabaseBackend` pour MariaDB,
via un pool de connexions. Le cœur découvre ce backend par entry point
(groupe ``forge_mvc.db_backend``) : il suffit que ce paquet soit installé.

Le pool est créé au premier emprunt de connexion (lazy init). L'import du
module ne produit aucun effet de bord réseau.
"""
import logging
import threading
from typing import Any

from core.forge import get as _cfg

from forge_mvc_mariadb.dialect import MariaDBDialect

logger = logging.getLogger(__name__)


class MariaDBBackend:
    """Backend BDD MariaDB : pool de connexions thread-safe."""

    name = "mariadb"
    dialect = MariaDBDialect()

    def __init__(self) -> None:
        self._pool: Any = None
        self._pool_lock = threading.Lock()

    def _get_pool(self) -> Any:
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    import mariadb
                    _mariadb: Any = mariadb
                    self._pool = _mariadb.ConnectionPool(
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
        return self._pool

    def get_connection(self) -> Any:
        """Emprunte une connexion depuis le pool (créé au premier appel)."""
        import mariadb
        _mariadb: Any = mariadb
        try:
            return self._get_pool().get_connection()
        except _mariadb.PoolError as error:
            logger.exception("Pool épuisé ou connexion impossible : %s", error)
            raise

    def close_connection(self, connection: Any) -> None:
        """Restitue la connexion au pool."""
        if connection is not None:
            connection.close()

    def close(self) -> None:
        """Ferme le pool sous-jacent (réinitialisation, fin de session de test)."""
        if self._pool is not None:
            try:
                self._pool.close()
            except Exception:  # noqa: BLE001 — fermeture best-effort
                pass
            self._pool = None
