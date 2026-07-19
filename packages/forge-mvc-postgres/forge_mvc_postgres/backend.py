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
from typing import Any

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
    """Connexion psycopg enveloppée, conforme aux attentes du cœur."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

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
        self._connection.close()

    @property
    def autocommit(self) -> Any:
        return self._connection.autocommit

    @autocommit.setter
    def autocommit(self, value: Any) -> None:
        self._connection.autocommit = value


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

    def get_connection(self) -> Any:
        import psycopg

        pg: Any = psycopg
        # ADR-060/ADR-066 : config de connexion runtime lue dans l'environnement
        # (DB_HOST/DB_PORT partagés, identifiants applicatifs distincts).
        host = os.environ.get("DB_HOST", "localhost")
        port = int(os.environ.get("DB_PORT", "5432"))
        dbname = os.environ.get("DB_NAME", "")
        user = os.environ.get("DB_APP_LOGIN", "")
        password = os.environ.get("DB_APP_PWD", "")
        conninfo = (
            f"host={host} port={port} "
            f"dbname={dbname} user={user} "
            f"password={password}"
        )
        raw: Any = pg.connect(conninfo)
        return _PgConnection(raw)

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
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
        if connection is not None:
            connection.close()
