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
    # Variables d'environnement lues par le backend (ADR-064). Amorcées par
    # `forge db:config` ; aucune valeur sensible ici (exemples ou vide).
    env_template: "list[tuple[str, str]]" = [
        ("# Nom de la base de données du projet.", ""),
        ("DB_NAME", ""),
        ("# Serveur SQL Server : hôte et port, partagés par les comptes admin et applicatif.", ""),
        ("DB_HOST", "127.0.0.1"),
        ("DB_PORT", "1433"),
        ("# Compte d'administration de la base du projet (droits sur DB_NAME, pas le compte sa serveur) : DDL, db:apply, migrations.", ""),
        ("DB_ADMIN_LOGIN", ""),
        ("DB_ADMIN_PWD", ""),
        ("# Compte applicatif : runtime, DML uniquement (SELECT, INSERT, UPDATE, DELETE).", ""),
        ("DB_APP_LOGIN", ""),
        ("DB_APP_PWD", ""),
        ("# Pilote ODBC installé sur la machine (voir la doc du backend).", ""),
        ("DB_ODBC_DRIVER", "ODBC Driver 18 for SQL Server"),
    ]

    def get_connection(self) -> Any:
        import pyodbc

        odbc: Any = pyodbc
        driver = os.environ.get("DB_ODBC_DRIVER", _DEFAULT_ODBC_DRIVER)
        # ADR-060/ADR-066 : config de connexion runtime lue dans l'environnement
        # (DB_HOST/DB_PORT partagés, identifiants applicatifs distincts).
        host = os.environ.get("DB_HOST", "localhost")
        port = int(os.environ.get("DB_PORT", "1433"))
        dbname = os.environ.get("DB_NAME", "")
        user = os.environ.get("DB_APP_LOGIN", "")
        password = os.environ.get("DB_APP_PWD", "")
        conn_str = (
            f"DRIVER={{{driver}}};"
            f"SERVER={host},{port};"
            f"DATABASE={dbname};"
            f"UID={user};PWD={password};"
            f"TrustServerCertificate=yes"
        )
        raw: Any = odbc.connect(conn_str)
        return _MsConnection(raw)

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        import pyodbc

        odbc: Any = pyodbc
        driver = os.environ.get("DB_ODBC_DRIVER", _DEFAULT_ODBC_DRIVER)
        # Serveur partagé (DB_HOST/DB_PORT) ; seuls les identifiants
        # d'administration sont distincts (ADR-066).
        host = os.environ.get("DB_HOST", "localhost")
        port = int(os.environ.get("DB_PORT", "1433"))
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
