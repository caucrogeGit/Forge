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
import os
import threading
from typing import Any

from core.forge import get as _cfg

from forge_mvc_mariadb.dialect import MariaDBDialect

logger = logging.getLogger(__name__)


class MariaDBBackend:
    """Backend BDD MariaDB : pool de connexions thread-safe."""

    name = "mariadb"
    dialect = MariaDBDialect()
    requires_provisioning = True
    # Variables d'environnement lues par le backend (ADR-064). Amorcées par
    # `forge db:config` ; aucune valeur sensible ici (exemples ou vide).
    env_template: "list[tuple[str, str]]" = [
        ("DB_NAME", ""),
        ("DB_APP_HOST", "127.0.0.1"),
        ("DB_APP_PORT", "3306"),
        ("DB_APP_LOGIN", ""),
        ("DB_APP_PWD", ""),
        ("DB_ADMIN_HOST", "127.0.0.1"),
        ("DB_ADMIN_PORT", "3306"),
        ("DB_ADMIN_LOGIN", ""),
        ("DB_ADMIN_PWD", ""),
    ]

    def __init__(self) -> None:
        self._pool: Any = None
        self._pool_lock = threading.Lock()

    def _get_pool(self) -> Any:
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    import mariadb
                    _mariadb: Any = mariadb
                    # ADR-060 : la config de connexion runtime est lue dans
                    # l'environnement (DB_APP_*, DB_NAME, DB_POOL_SIZE).
                    db_name = os.environ.get("DB_NAME", "")
                    pool_size = int(os.environ.get("DB_POOL_SIZE", "5"))
                    self._pool = _mariadb.ConnectionPool(
                        host      = os.environ.get("DB_APP_HOST", "localhost"),
                        port      = int(os.environ.get("DB_APP_PORT", "3306")),
                        user      = os.environ.get("DB_APP_LOGIN", ""),
                        password  = os.environ.get("DB_APP_PWD", ""),
                        database  = db_name,
                        pool_name = str(_cfg("app_name")).lower(),
                        pool_size = pool_size,
                    )
                    logger.debug("Pool MariaDB initialisé (%s, taille=%s)",
                                 db_name, pool_size)
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

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        """Connexion d'administration directe, hors pool.

        Les identifiants d'administration sont lus dans l'environnement
        (`DB_ADMIN_HOST/PORT/LOGIN/PWD`, ADR-060). `database=None` pour `db:init`
        (la base n'existe pas encore) ; renseigné pour `db:apply` et les migrations.
        """
        import mariadb
        _mariadb: Any = mariadb
        kwargs: dict[str, Any] = {
            "host": os.environ.get("DB_ADMIN_HOST", "localhost"),
            "port": int(os.environ.get("DB_ADMIN_PORT", "3306")),
            "user": os.environ.get("DB_ADMIN_LOGIN", ""),
            "password": os.environ.get("DB_ADMIN_PWD", ""),
        }
        if database is not None:
            kwargs["database"] = database
        return _mariadb.connect(**kwargs)

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
