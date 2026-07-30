# pyright: strict
# psycopg est une dépendance optionnelle (installée avec ce paquet) ; le cœur
# et l'usage du dialecte ne l'importent pas. On tolère son absence à l'analyse
# statique et on aliase ses membres en Any localement.
# pyright: reportMissingTypeStubs=false, reportMissingImports=false, reportMissingModuleSource=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
forge_mvc_postgres.backend — Backend BDD PostgreSQL pour Forge (ADR-054)
=======================================================================
Adaptateur au-dessus de psycopg (v3). PostgreSQL est client-serveur : ce
backend est un client ; un serveur PostgreSQL doit être joignable.

Le cœur attend des connexions compatibles « à la MariaDB » : curseur avec
``dictionary=...``, ``commit``/``rollback``/``close``, l'attribut
``autocommit``, et sur le curseur ``execute``/``fetchone``/``fetchall``/
``lastrowid``/``rowcount``. psycopg utilise le format de paramètres « %s » :
l'adaptateur traduit les « ? » de Forge à l'exécution (voir translate).

Niveau plein (promotion ADR-084) : dialecte, provisioning `db:init` et
intégration (couche DB, migrations, introspection) validés en CI contre un
vrai serveur PostgreSQL.
psycopg est importé paresseusement (l'usage du dialecte ne le requiert pas).
"""
import logging
import os
import threading
from typing import Any

from core.database.errors import DatabaseUnavailableError

from forge_mvc_postgres.dialect import PostgreSQLDialect
from forge_mvc_postgres.translate import translate_placeholders

logger = logging.getLogger(__name__)


class _PgCursor:
    """Curseur psycopg enveloppé : traduit « ? » et expose lastrowid."""

    def __init__(self, cursor: Any) -> None:
        self._cursor = cursor

    def execute(self, sql: str, params: "Any" = ()) -> "_PgCursor":
        self._cursor.execute(translate_placeholders(sql), tuple(params))
        return self

    @property
    def lastrowid(self) -> "int | None":
        # PostgreSQL n'a pas de lastrowid ; lastval() renvoie la dernière valeur
        # de séquence générée dans la session (PK identity/serial, le modèle des
        # tables Forge). PG-INSERT-IDENTITY-001 : si aucune séquence n'a été
        # touchée, lastval() lève une erreur qui, en bloc de transaction,
        # avorterait la transaction et ferait perdre l'INSERT au commit. La
        # lecture est donc protégée par un savepoint, restauré en cas d'échec.
        try:
            self._cursor.execute("SAVEPOINT forge_lastrowid")
        except Exception:
            # Hors bloc de transaction (autocommit) : un échec de lastval()
            # n'avorte rien, lecture directe sans garde.
            return self._read_lastval()
        value = self._read_lastval()
        # Les erreurs de gestion du savepoint sont volontairement avalées : ce
        # chemin ne doit jamais faire échouer une insertion acquise, et une
        # connexion réellement morte resurgira au commit.
        if value is None:
            try:
                self._cursor.execute("ROLLBACK TO SAVEPOINT forge_lastrowid")
            except Exception:
                pass
        else:
            try:
                self._cursor.execute("RELEASE SAVEPOINT forge_lastrowid")
            except Exception:
                pass
        return value

    def _read_lastval(self) -> "int | None":
        try:
            self._cursor.execute("SELECT lastval()")
            row = self._cursor.fetchone()
        except Exception:
            # « lastval is not yet defined in this session » : INSERT dans une
            # table sans colonne à séquence. L'identité est indéterminable.
            return None
        if row and row[0] is not None:
            return int(row[0])
        return None

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def fetchone(self) -> "Any":
        return self._cursor.fetchone()

    def fetchall(self) -> "Any":
        return self._cursor.fetchall()

    def close(self) -> None:
        self._cursor.close()


class _PgConnection:
    """Connexion psycopg enveloppée, conforme aux attentes du cœur.

    L'enveloppe sait d'où elle vient, et `close()` l'y renvoie : au pool si
    elle en a été empruntée, au néant sinon. Sans cela, fermer une connexion
    empruntée brûlait sa place définitivement, le pool ignorant qu'elle avait
    disparu. Le piège n'est pas théorique, Forge y est tombé dans ses propres
    tests d'intégration dès l'arrivée du pool (POSTGRES-POOL-001), et c'est en
    outre le comportement du pilote MariaDB, dont `close()` restitue aussi.

    La restitution n'a lieu qu'une fois : rendre deux fois la même connexion
    corromprait le compte du pool.
    """

    def __init__(self, connection: Any, *, pool: Any = None) -> None:
        self._connection = connection
        self._pool = pool
        self._returned = False

    @property
    def pooled(self) -> bool:
        """Vrai si cette connexion doit retourner au pool plutôt que se fermer."""
        return self._pool is not None

    @property
    def raw(self) -> Any:
        """Connexion psycopg sous-jacente."""
        return self._connection

    def cursor(self, *, dictionary: bool = False) -> _PgCursor:
        if dictionary:
            import psycopg.rows

            rows: Any = psycopg.rows
            return _PgCursor(self._connection.cursor(row_factory=rows.dict_row))
        return _PgCursor(self._connection.cursor())

    def commit(self) -> None:
        self._connection.commit()

    def rollback(self) -> None:
        self._connection.rollback()

    def close(self) -> None:
        if self._pool is None:
            self._connection.close()
            return
        if not self._returned:
            self._returned = True
            self._pool.putconn(self._connection)

    @property
    def autocommit(self) -> Any:
        return self._connection.autocommit

    @autocommit.setter
    def autocommit(self, value: Any) -> None:
        self._connection.autocommit = value


def _reset_connection(connection: Any) -> None:
    """Rend la connexion vierge avant qu'elle ne reparte au pool.

    Le pool de psycopg annule bien la transaction en cours, mais rien d'autre :
    mesuré, une table temporaire et un `application_name` posés par une requête
    restaient visibles de l'emprunteur suivant. MariaDB, lui, isole
    complètement ses emprunts, angle vérifié sain au troisième cycle de
    pré-mortem : doter PostgreSQL d'un pool sans cette remise à zéro aurait
    introduit une fuite d'état là où il n'y en avait pas, chaque requête
    ouvrant jusque là sa propre connexion (POSTGRES-POOL-001).

    Le nettoyage est celui de `DISCARD ALL`, **moins** les requêtes préparées.
    Mesuré, les inclure casse la connexion suivante : `DISCARD ALL` exécute un
    `DEALLOCATE ALL` côté serveur, alors que psycopg tient son propre catalogue
    des requêtes qu'il a préparées. Il en réclame ensuite une que le serveur ne
    connaît plus, et rend « l'instruction préparée _pg3_0 n'existe pas ». Ce
    catalogue appartient au pilote, on ne le vide pas dans son dos ; et rien ne
    fuit à le laisser, une requête préparée n'étant ni une donnée ni un réglage.

    Les instructions retenues refusent de s'exécuter dans une transaction, d'où
    l'annulation puis le passage temporaire en autocommit. Elles partent en un
    seul lot, ce que psycopg autorise en l'absence de paramètre : mesuré,
    0,117 ms contre 0,540 ms envoyées une à une, sur une restitution qui a lieu
    à chaque requête HTTP.
    """
    connection.rollback()
    previous = connection.autocommit
    connection.autocommit = True
    try:
        connection.execute(
            "CLOSE ALL;"          # curseurs restés ouverts
            " RESET ALL;"         # variables de session (SET application_name...)
            " DISCARD PLANS;"     # plans mis en cache
            " DISCARD SEQUENCES;"
            " DISCARD TEMP"       # tables temporaires
        )
    finally:
        connection.autocommit = previous


class PostgreSQLBackend:
    """Backend BDD PostgreSQL (psycopg)."""

    name = "postgres"
    dialect = PostgreSQLDialect()
    requires_provisioning = True
    # Variables d'environnement lues par le backend (ADR-064). Amorcées par
    # `forge db:config` ; aucune valeur sensible ici (exemples ou vide).
    env_template: "list[tuple[str, str]]" = [
        ("# Nom de la base de données du projet.", ""),
        ("DB_NAME", ""),
        ("# Serveur PostgreSQL : hôte et port, partagés par les comptes admin et applicatif.", ""),
        ("DB_HOST", "127.0.0.1"),
        ("DB_PORT", "5432"),
        ("# Compte d'administration de la base du projet (droits sur DB_NAME, pas le superutilisateur serveur) : DDL, db:apply, migrations.", ""),
        ("DB_ADMIN_LOGIN", ""),
        ("DB_ADMIN_PWD", ""),
        ("# Compte applicatif : runtime, DML uniquement (SELECT, INSERT, UPDATE, DELETE).", ""),
        ("DB_APP_LOGIN", ""),
        ("DB_APP_PWD", ""),
    ]

    def __init__(self) -> None:
        self._pool: Any = None
        self._pool_lock = threading.Lock()

    def _runtime_conninfo(self) -> str:
        # ADR-060/ADR-066 : config de connexion runtime lue dans l'environnement
        # (DB_HOST/DB_PORT partagés, identifiants applicatifs distincts).
        host = os.environ.get("DB_HOST", "localhost")
        port = int(os.environ.get("DB_PORT", "5432"))
        dbname = os.environ.get("DB_NAME", "")
        user = os.environ.get("DB_APP_LOGIN", "")
        password = os.environ.get("DB_APP_PWD", "")
        return (
            f"host={host} port={port} "
            f"dbname={dbname} user={user} "
            f"password={password}"
        )

    def _get_pool(self) -> Any:
        """Crée le pool au premier emprunt, jamais à l'import (POSTGRES-POOL-001).

        La paresse n'est pas une commodité, c'est une nécessité : un pool né
        avant le `fork` de gunicorn serait partagé entre les processus fils,
        chacun croyant disposer de connexions que les autres utilisent. Créé au
        premier emprunt, il naît dans le fils, comme celui de MariaDB.
        """
        if self._pool is None:
            with self._pool_lock:
                if self._pool is None:
                    from psycopg_pool import ConnectionPool

                    pool_class: Any = ConnectionPool
                    size = max(1, int(os.environ.get("DB_POOL_SIZE", "5")))
                    timeout = float(os.environ.get("DB_POOL_TIMEOUT", "5"))
                    self._pool = pool_class(
                        conninfo=self._runtime_conninfo(),
                        min_size=1,
                        max_size=size,
                        timeout=timeout,
                        # Revalidation avant remise en circulation : le serveur
                        # peut avoir fermé la connexion de son côté pendant
                        # qu'elle dormait dans le pool. Une requête vide coûte
                        # une fraction de milliseconde, contre les douze que
                        # coûtait l'ouverture d'une connexion neuve.
                        check=pool_class.check_connection,
                        # Remise à zéro de l'état de session à la restitution,
                        # sans quoi tables temporaires et variables de session
                        # passeraient d'un emprunteur au suivant.
                        reset=_reset_connection,
                        name=os.environ.get("DB_NAME", "forge") or "forge",
                        open=True,
                    )
                    logger.debug("Pool PostgreSQL initialisé (taille=%s)", size)
        return self._pool

    def get_connection(self) -> Any:
        """Emprunte une connexion au pool, en patientant s'il est saturé.

        Avant ce pool, chaque requête ouvrait puis fermait une connexion
        (POSTGRES-POOL-001). Mesuré sur serveur local, 12,12 ms contre 0,16 ms
        sur une connexion déjà ouverte, soit un facteur 78 : une page à dix
        requêtes payait 120 ms de connexion pure. MariaDB avait son pool et SQL
        Server bénéficie de celui du gestionnaire ODBC ; PostgreSQL était le
        seul à repartir de zéro à chaque fois. `DB_POOL_SIZE` et
        `DB_POOL_TIMEOUT` y étaient de surcroît ignorés en silence.

        L'attente est bornée par `DB_POOL_TIMEOUT` (5 s par défaut). Au delà,
        `DatabaseUnavailableError` est levée, comme chez MariaDB : c'est une
        surcharge, pas une panne, et le cœur la traduit en 503.
        """
        from psycopg_pool import PoolTimeout

        pool = self._get_pool()
        try:
            raw: Any = pool.getconn()
        except PoolTimeout as error:
            logger.warning(
                "Pool PostgreSQL saturé : aucune connexion libérée en %ss "
                "(DB_POOL_SIZE=%s). Élargissez le pool ou raccourcissez les requêtes.",
                os.environ.get("DB_POOL_TIMEOUT", "5"),
                os.environ.get("DB_POOL_SIZE", "5"),
            )
            raise DatabaseUnavailableError(str(error)) from error
        return _PgConnection(raw, pool=pool)

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        """Connexion d'administration, ouverte en direct et **hors pool**.

        Le pool sert l'exécution, avec les identifiants applicatifs et une
        taille dimensionnée pour le trafic HTTP. L'administration est d'une
        autre nature : rare, ponctuelle, sous d'autres identifiants (ADR-033),
        et parfois dirigée vers une autre base que celle du projet. La faire
        passer par le pool mélangerait deux comptes dans un même jeu de
        connexions réutilisées.

        Sa restitution la ferme donc, au lieu de la rendre au pool.
        """
        import psycopg

        pg: Any = psycopg
        # Serveur partagé (DB_HOST/DB_PORT) ; seuls les identifiants
        # d'administration sont distincts (ADR-066).
        host = os.environ.get("DB_HOST", "localhost")
        port = int(os.environ.get("DB_PORT", "5432"))
        login = os.environ.get("DB_ADMIN_LOGIN", "")
        password = os.environ.get("DB_ADMIN_PWD", "")
        # `db:init` (database=None) se connecte à la base de maintenance
        # « postgres » pour créer la base du projet.
        dbname = database or "postgres"
        conninfo = (
            f"host={host} port={port} dbname={dbname} "
            f"user={login} password={password}"
        )
        raw: Any = pg.connect(conninfo)
        return _PgConnection(raw)

    def close_connection(self, connection: Any) -> None:
        """Rend la connexion au pool, ou la ferme si elle n'en vient pas.

        L'aiguillage appartient à l'enveloppe, qui seule sait d'où elle vient :
        une connexion d'administration est ouverte en direct, hors pool, et la
        restituer à un pool qui ne l'a jamais prêtée le corromprait. Le faire
        ici sur un attribut plutôt que là-bas laisserait un `close()` direct
        brûler une place, ce qui est arrivé.
        """
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

    def is_unique_violation(self, error: Exception) -> bool:
        """Doublon PostgreSQL : SQLSTATE 23505 (`unique_violation`).

        Le seul backend où le SQLSTATE discrimine réellement, PostgreSQL
        distinguant 23505 (unicité), 23503 (clé étrangère) et 23502 (NOT NULL).
        psycopg expose en plus la classe dédiée `errors.UniqueViolation` ; on
        teste le SQLSTATE, qui couvre aussi les exceptions reconstruites.
        """
        return getattr(error, "sqlstate", None) == "23505"

    def is_unavailable(self, error: Exception) -> bool:
        """Indisponibilité PostgreSQL : classe SQLSTATE 08, arrêts 57Pxx.

        La classe `08` est celle des « connection exception » de la norme.
        S'y ajoutent les arrêts décidés par le serveur, mesurés : `57P01`
        (`admin_shutdown`, rendu quand le backend est terminé), `57P02`
        (`crash_shutdown`) et `57P03` (`cannot_connect_now`, redémarrage en
        cours).

        Un troisième cas n'a pas de SQLSTATE du tout : une fois la connexion
        constatée morte, psycopg lève une `OperationalError` née côté client,
        sans réponse du serveur donc sans code. Mesuré, la deuxième requête
        après coupure donne « the connection is lost », `sqlstate` à `None`.
        L'absence de SQLSTATE **sur une `OperationalError`** est justement le
        signal que l'erreur ne vient pas du serveur ; les erreurs de requête,
        elles, en portent toujours un.
        """
        import psycopg

        sqlstate = getattr(error, "sqlstate", None)
        if isinstance(sqlstate, str):
            return sqlstate.startswith("08") or sqlstate in {"57P01", "57P02", "57P03"}
        return isinstance(error, psycopg.OperationalError)
