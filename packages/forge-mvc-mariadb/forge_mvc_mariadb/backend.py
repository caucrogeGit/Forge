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

from core.database.errors import DatabaseUnavailableError
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
        ("# Nom de la base de données du projet.", ""),
        ("DB_NAME", ""),
        ("# Serveur MariaDB : hôte et port, partagés par les comptes admin et applicatif.", ""),
        ("DB_HOST", "127.0.0.1"),
        ("DB_PORT", "3306"),
        ("# Compte d'administration de la base du projet (droits sur DB_NAME, pas le root serveur) : DDL, db:apply, migrations.", ""),
        ("DB_ADMIN_LOGIN", ""),
        ("DB_ADMIN_PWD", ""),
        ("# Compte applicatif : runtime, DML uniquement (SELECT, INSERT, UPDATE, DELETE).", ""),
        ("DB_APP_LOGIN", ""),
        ("DB_APP_PWD", ""),
        ("# Pool de connexions : nombre de places, et attente avant de rendre un 503.", ""),
        ("DB_POOL_SIZE", "5"),
        ("DB_POOL_TIMEOUT", "5"),
    ]

    def __init__(self) -> None:
        self._pool: Any = None
        self._pool_lock = threading.Lock()
        # File d'attente devant le pool (MARIADB-POOL-QUEUE-001). Créée avec le
        # pool, elle porte autant de jetons que de connexions : un emprunteur
        # patiente au lieu d'échouer quand toutes sont prises.
        self._gate: "threading.BoundedSemaphore | None" = None

    def _get_pool(self) -> Any:
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    import mariadb
                    _mariadb: Any = mariadb
                    # ADR-060/ADR-066 : la config de connexion runtime est lue
                    # dans l'environnement (DB_HOST/DB_PORT partagés, DB_APP_LOGIN,
                    # DB_APP_PWD, DB_NAME, DB_POOL_SIZE).
                    db_name = os.environ.get("DB_NAME", "")
                    pool_size = int(os.environ.get("DB_POOL_SIZE", "5"))
                    self._pool = _mariadb.ConnectionPool(
                        host      = os.environ.get("DB_HOST", "localhost"),
                        port      = int(os.environ.get("DB_PORT", "3306")),
                        user      = os.environ.get("DB_APP_LOGIN", ""),
                        password  = os.environ.get("DB_APP_PWD", ""),
                        database  = db_name,
                        pool_name = str(_cfg("app_name")).lower(),
                        pool_size = pool_size,
                    )
                    self._gate = threading.BoundedSemaphore(pool_size)
                    logger.debug("Pool MariaDB initialisé (%s, taille=%s)",
                                 db_name, pool_size)
        return self._pool

    def get_connection(self) -> Any:
        """Emprunte une connexion, en patientant si le pool est saturé.

        Le pilote MariaDB n'offre aucune file d'attente : son
        ``get_connection()`` lève immédiatement dès que toutes les connexions
        sont prises. Mesuré, cela faisait échouer 7 requêtes sur 20 arrivées
        au même instant, alors que chacune ne durait qu'un quart de
        milliseconde et qu'attendre quelques millisecondes suffisait.

        Un sémaphore aux jetons du pool rétablit l'attente. Il en faut un vrai,
        et non une boucle de réessais : mesuré, 200 emprunteurs interrogeant le
        pool en boucle se disputent son verrou et **aggravent** la situation
        (170 échecs sur 200, contre 146 sans attente).

        L'attente est bornée par ``DB_POOL_TIMEOUT`` (5 s par défaut). Au delà,
        `DatabaseUnavailableError` est levée : c'est une surcharge, pas une
        panne, et le cœur la traduit en 503.
        """
        import mariadb
        _mariadb: Any = mariadb

        pool = self._get_pool()
        gate = self._gate
        if gate is None:  # pragma: no cover - le pool crée toujours la file
            return pool.get_connection()

        timeout = float(os.environ.get("DB_POOL_TIMEOUT", "5"))
        if not gate.acquire(timeout=timeout):
            logger.warning(
                "Pool MariaDB saturé : aucune connexion libérée en %.1fs "
                "(DB_POOL_SIZE=%s). Élargissez le pool ou raccourcissez les requêtes.",
                timeout, os.environ.get("DB_POOL_SIZE", "5"),
            )
            raise DatabaseUnavailableError(
                f"Aucune connexion disponible après {timeout:.1f}s d'attente."
            )

        try:
            return pool.get_connection()
        except BaseException as error:
            # Le jeton doit repartir : sans cela, un échec d'emprunt réduirait
            # définitivement la capacité de la file.
            gate.release()
            if isinstance(error, _mariadb.PoolError):
                logger.exception("Emprunt impossible malgré un jeton libre : %s", error)
                raise DatabaseUnavailableError(str(error)) from error
            raise

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        """Connexion d'administration directe, hors pool.

        Le serveur est décrit par `DB_HOST`/`DB_PORT` (partagés avec la connexion
        applicative, ADR-066) ; seuls les identifiants d'administration
        (`DB_ADMIN_LOGIN`/`DB_ADMIN_PWD`, ADR-033) sont distincts. `database=None`
        pour `db:init` (la base n'existe pas encore) ; renseigné pour `db:apply`
        et les migrations.
        """
        import mariadb
        _mariadb: Any = mariadb
        kwargs: dict[str, Any] = {
            "host": os.environ.get("DB_HOST", "localhost"),
            "port": int(os.environ.get("DB_PORT", "3306")),
            "user": os.environ.get("DB_ADMIN_LOGIN", ""),
            "password": os.environ.get("DB_ADMIN_PWD", ""),
        }
        if database is not None:
            kwargs["database"] = database
        return _mariadb.connect(**kwargs)

    def close_connection(self, connection: Any) -> None:
        """Restitue la connexion au pool, puis le jeton à la file d'attente.

        Dans cet ordre : le jeton ne doit repartir qu'une fois la connexion
        réellement disponible, sans quoi l'emprunteur suivant se présenterait
        devant un pool encore plein.

        La file est **bornée** : une restitution sans emprunt lève, plutôt que
        d'enfler silencieusement la capacité.
        """
        if connection is None:
            return
        try:
            connection.close()
        finally:
            if self._gate is not None:
                self._gate.release()

    def is_unique_violation(self, error: Exception) -> bool:
        """Doublon MariaDB : errno 1062 (ER_DUP_ENTRY).

        Le SQLSTATE ne convient pas : MariaDB renvoie `23000` aussi bien pour
        un doublon que pour un NOT NULL (errno 1048). Seul l'errno discrimine.
        """
        return getattr(error, "errno", None) == 1062

    def is_unavailable(self, error: Exception) -> bool:
        """Indisponibilité MariaDB : la connexion coupée, ou le verrou tenu ailleurs.

        **La connexion coupée.** `2006` (« Server has gone away ») et `2013`
        (« Lost connection to server during query ») sont les deux formes
        rendues selon que la coupure est constatée avant ou pendant la requête.
        On y joint les errno d'établissement `2002`/`2003` et `2055`, du même
        registre : le serveur est hors d'atteinte, la requête n'a rien de
        fautif.

        **La ressource prise.** `1205` (« Lock wait timeout exceeded »)
        signale qu'une autre transaction tient le verrou depuis plus longtemps
        que `innodb_lock_wait_timeout`. C'est de la contention pure, le jumeau
        du verrou de fichier SQLite et de la saturation du pool : attendre
        suffit, et l'appel suivant passera.

        Ce que cette méthode **ne** reconnaît pas, et pourquoi. L'interblocage,
        errno `1213` et SQLSTATE `40001`, sort de la famille bien qu'il soit
        transitoire lui aussi : le critère est « attendre suffit », or attendre
        n'y change rien. Deux transactions ont pris leurs verrous dans des
        ordres incompatibles, InnoDB en a annulé une, et le remède est de
        revoir cet ordre. Le 500 le laisse visible dans les journaux d'erreur,
        là où un 503 le rangerait parmi les conditions de routine et rendrait
        un défaut d'ordonnancement récurrent invisible
        (MARIADB-LOCK-WAIT-503-001).

        Le SQLSTATE ne discrimine pas la coupure ni l'attente : ces erreurs
        portent `HY000`, fourre-tout du pilote. Seul l'errno sert, comme pour
        le doublon. Signaux relevés en tuant la connexion, puis en tenant un
        verrou depuis une seconde transaction.
        """
        return getattr(error, "errno", None) in {1205, 2002, 2003, 2006, 2013, 2055}

    def close(self) -> None:
        """Ferme le pool sous-jacent (réinitialisation, fin de session de test)."""
        if self._pool is not None:
            try:
                self._pool.close()
            except Exception:  # noqa: BLE001 — fermeture best-effort
                pass
            self._pool = None
