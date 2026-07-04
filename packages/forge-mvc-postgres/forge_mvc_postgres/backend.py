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

Statut Alpha : la logique (dialecte, traduction) est testée unitairement ;
l'intégration serveur et le provisioning CLI restent à valider/câbler.
psycopg est importé paresseusement (l'usage du dialecte ne le requiert pas).
"""
import logging
import os
from typing import Any

from core.forge import get as _cfg

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
        # de séquence générée dans la session (insertion dans une colonne serial).
        self._cursor.execute("SELECT lastval()")
        row = self._cursor.fetchone()
        return row[0] if row else None

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

    def get_connection(self) -> Any:
        import psycopg

        pg: Any = psycopg
        conninfo = (
            f"host={_cfg('db_host')} port={_cfg('db_port')} "
            f"dbname={_cfg('db_name')} user={_cfg('db_user')} "
            f"password={_cfg('db_password')}"
        )
        raw: Any = pg.connect(conninfo)
        return _PgConnection(raw)

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        import psycopg

        pg: Any = psycopg
        # Identifiants d'administration lus dans l'environnement (ADR-060).
        host = os.environ.get("DB_ADMIN_HOST", "localhost")
        port = int(os.environ.get("DB_ADMIN_PORT", "5432"))
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
