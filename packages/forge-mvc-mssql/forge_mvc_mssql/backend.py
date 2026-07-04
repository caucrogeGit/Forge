# pyright: strict
# pyodbc est une dépendance optionnelle (installée avec ce paquet) et requiert
# un pilote ODBC système ; le cœur et l'usage du dialecte ne l'importent pas. On
# tolère son absence à l'analyse statique et on aliase ses membres en Any.
# pyright: reportMissingTypeStubs=false, reportMissingImports=false, reportMissingModuleSource=false
# pyright: reportUnknownMemberType=false, reportUnknownVariableType=false, reportUnknownArgumentType=false
"""
forge_mvc_mssql.backend — Backend BDD Microsoft SQL Server pour Forge (ADR-054)
==============================================================================
Adaptateur au-dessus de pyodbc. SQL Server est client-serveur : ce backend est
un client (via un pilote ODBC) ; un serveur SQL Server doit être joignable.

pyodbc utilise nativement les paramètres « ? » de Forge : aucune traduction.
Le cœur attend un curseur avec ``dictionary=...``, ``commit``/``rollback``/
``close``, ``autocommit``, et sur le curseur ``execute``/``fetchone``/
``fetchall``/``lastrowid``/``rowcount``. pyodbc ne renvoie pas de dicts ni de
lastrowid : l'adaptateur convertit via ``cursor.description`` et lit l'identité
via ``SCOPE_IDENTITY()``.

Statut Alpha : la logique (dialecte) est testée unitairement ; l'intégration
serveur et le provisioning CLI restent à valider/câbler. pyodbc est importé
paresseusement (l'usage du dialecte ne le requiert pas).

Pilote ODBC : par défaut « ODBC Driver 18 for SQL Server », surchargeable via la
variable d'environnement ``DB_ODBC_DRIVER``.
"""
import logging
import os
from typing import Any

from core.forge import get as _cfg

from forge_mvc_mssql.dialect import MSSQLDialect

logger = logging.getLogger(__name__)

_DEFAULT_ODBC_DRIVER = "ODBC Driver 18 for SQL Server"


class _MsCursor:
    """Curseur pyodbc enveloppé : lignes-dict optionnelles et lastrowid."""

    def __init__(self, cursor: Any, dictionary: bool) -> None:
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, sql: str, params: "Any" = ()) -> "_MsCursor":
        bound = tuple(params)
        if bound:
            self._cursor.execute(sql, bound)
        else:
            self._cursor.execute(sql)
        return self

    def _columns(self) -> "list[str]":
        return [col[0] for col in self._cursor.description]

    def fetchone(self) -> "Any":
        row = self._cursor.fetchone()
        if row is None:
            return None
        if self._dictionary:
            return dict(zip(self._columns(), row))
        return row

    def fetchall(self) -> "Any":
        rows = self._cursor.fetchall()
        if self._dictionary:
            columns = self._columns()
            return [dict(zip(columns, row)) for row in rows]
        return rows

    @property
    def lastrowid(self) -> "int | None":
        # SQL Server n'a pas de lastrowid ; SCOPE_IDENTITY() renvoie la dernière
        # valeur d'identité générée dans la portée courante.
        self._cursor.execute("SELECT SCOPE_IDENTITY()")
        row = self._cursor.fetchone()
        if row and row[0] is not None:
            return int(row[0])
        return None

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def close(self) -> None:
        self._cursor.close()


class _MsConnection:
    """Connexion pyodbc enveloppée, conforme aux attentes du cœur."""

    def __init__(self, connection: Any) -> None:
        self._connection = connection

    def cursor(self, *, dictionary: bool = False) -> _MsCursor:
        return _MsCursor(self._connection.cursor(), dictionary)

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


class MSSQLBackend:
    """Backend BDD Microsoft SQL Server (pyodbc)."""

    name = "mssql"
    dialect = MSSQLDialect()
    requires_provisioning = True

    def get_connection(self) -> Any:
        import pyodbc

        odbc: Any = pyodbc
        driver = os.environ.get("DB_ODBC_DRIVER", _DEFAULT_ODBC_DRIVER)
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={_cfg('db_host')},{_cfg('db_port')};"
            f"DATABASE={_cfg('db_name')};"
            f"UID={_cfg('db_user')};PWD={_cfg('db_password')};"
            f"TrustServerCertificate=yes"
        )
        raw: Any = odbc.connect(conn_str)
        return _MsConnection(raw)

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        import pyodbc

        odbc: Any = pyodbc
        driver = os.environ.get("DB_ODBC_DRIVER", _DEFAULT_ODBC_DRIVER)
        # Identifiants d'administration lus dans l'environnement (ADR-060).
        host = os.environ.get("DB_ADMIN_HOST", "localhost")
        port = int(os.environ.get("DB_ADMIN_PORT", "1433"))
        login = os.environ.get("DB_ADMIN_LOGIN", "")
        password = os.environ.get("DB_ADMIN_PWD", "")
        # `db:init` (database=None) se connecte à la base de maintenance
        # « master » pour créer la base du projet.
        db = database or "master"
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={db};"
            f"UID={login};PWD={password};"
            f"TrustServerCertificate=yes"
        )
        raw: Any = odbc.connect(conn_str)
        return _MsConnection(raw)

    def close_connection(self, connection: Any) -> None:
        if connection is not None:
            connection.close()
