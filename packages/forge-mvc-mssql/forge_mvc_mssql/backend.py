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
via ``SCOPE_IDENTITY()`` exécuté dans le même lot que l'INSERT
(MSSQL-INSERT-IDENTITY-001 : dans un lot séparé, ``SCOPE_IDENTITY()`` sort de
la portée de l'INSERT et renvoie toujours NULL).

Niveau plein (promotion ADR-084) : dialecte, provisioning `db:init` et
intégration (couche DB, migrations, introspection) validés en CI contre un
vrai serveur SQL Server. pyodbc est importé paresseusement (l'usage du
dialecte ne le requiert pas).

Pilote ODBC : par défaut « ODBC Driver 18 for SQL Server », surchargeable via la
variable d'environnement ``DB_ODBC_DRIVER``.
"""
import logging
import os
import re
from typing import Any

from core.database.sql_script import split_sql_statements

from forge_mvc_mssql.dialect import MSSQLDialect

logger = logging.getLogger(__name__)

_DEFAULT_ODBC_DRIVER = "ODBC Driver 18 for SQL Server"

# Détection d'un INSERT à identité récupérable : la lecture de SCOPE_IDENTITY()
# doit se faire dans le même lot (batch) que l'INSERT. On ne réécrit pas les
# statements qui gèrent déjà leur identité (OUTPUT ... INSERTED, appel explicite
# à SCOPE_IDENTITY()).
#
# Ces motifs ne s'appliquent JAMAIS au SQL brut, mais à son squelette de
# mots-clés (voir `_keyword_skeleton`) : lus sur le texte tel quel, ils
# répondaient faux quatre fois sur sept (MSSQL-INSERT-IDENTITY-SCOPE-001).
_INSERT_STATEMENT = re.compile(r"^\s*insert\b", re.IGNORECASE)
_HANDLES_IDENTITY = re.compile(r"\boutput\b|\bscope_identity\b", re.IGNORECASE)

# Appliqués à un texte déjà débarrassé de ses commentaires par le découpeur
# canonique : aucun `'` ni `]` égaré ne peut donc leur échapper.
_STRING_LITERAL = re.compile(r"'(?:[^']|'')*'")
_BRACKET_IDENTIFIER = re.compile(r"\[[^\]]*\]")
_QUOTED_IDENTIFIER = re.compile(r'"[^"]*"')


def _keyword_skeleton(sql: str) -> str:
    """Rend le SQL réduit à ses mots-clés, pour y chercher sans se tromper.

    Trois formes de texte y ressemblent à du code sans en être : les
    commentaires, les littéraux de chaîne et les identifiants délimités. Le
    découpeur canonique du cœur (ADR-079) ôte les premiers en respectant les
    seconds, ce qui permet ensuite de vider littéraux et identifiants par
    simple expression régulière : sans commentaire, plus aucune apostrophe ni
    aucun crochet ne peut être orphelin.

    Ce que cela corrige, mesuré sur serveur réel : quatre formes d'INSERT sur
    sept perdaient leur identité en silence, la ligne étant pourtant écrite.
    Un commentaire **avant** l'INSERT le déguisait en autre chose ; le mot
    « output » dans un littéral ou un commentaire le faisait passer pour un
    statement gérant déjà son identité, tout comme une colonne légitimement
    nommée `[output]`.
    """
    skeleton = " ; ".join(split_sql_statements(sql))
    skeleton = _STRING_LITERAL.sub("''", skeleton)
    skeleton = _BRACKET_IDENTIFIER.sub("[]", skeleton)
    return _QUOTED_IDENTIFIER.sub('""', skeleton)


def _needs_identity_batch(sql: str) -> bool:
    """Vrai si l'identité de cet INSERT doit être lue dans son propre lot.

    Limite assumée : un INSERT précédé d'une expression de table commune
    (`WITH ... INSERT`) n'est pas reconnu, la forme n'étant pas ancrée en tête.
    `lastrowid` y reste None, comme avant, plutôt que de risquer un lot
    invalide sur une reconnaissance approximative.
    """
    skeleton = _keyword_skeleton(sql)
    if not _INSERT_STATEMENT.match(skeleton):
        return False
    return not _HANDLES_IDENTITY.search(skeleton)


class _MsCursor:
    """Curseur pyodbc enveloppé : lignes-dict optionnelles et lastrowid."""

    def __init__(self, cursor: Any, dictionary: bool) -> None:
        self._cursor = cursor
        self._dictionary = dictionary
        self._lastrowid: "int | None" = None
        self._insert_rowcount: "int | None" = None

    def execute(self, sql: str, params: "Any" = ()) -> "_MsCursor":
        self._lastrowid = None
        self._insert_rowcount = None
        if _needs_identity_batch(sql):
            return self._execute_insert(sql, params)
        bound = tuple(params)
        if bound:
            self._cursor.execute(sql, bound)
        else:
            self._cursor.execute(sql)
        return self

    def _execute_insert(self, sql: str, params: "Any") -> "_MsCursor":
        # SCOPE_IDENTITY() n'est défini que dans la portée (le lot) qui a
        # exécuté l'INSERT : un execute() séparé renverrait toujours NULL. On
        # exécute donc l'INSERT et la lecture d'identité dans le même lot, puis
        # on mémorise le rowcount de l'INSERT (avant de passer au résultat du
        # SELECT) et l'identité, servis par `rowcount` et `lastrowid`.
        #
        # La lecture commence sur une ligne neuve : collée à la suite, elle
        # disparaissait dans un commentaire de fin de ligne, et le lot se
        # réduisait au seul INSERT (MSSQL-INSERT-IDENTITY-SCOPE-001). Le texte
        # d'origine est par ailleurs conservé tel quel, commentaires compris :
        # c'est lui qui atteint le serveur, et donc le journal du DBA.
        batch = sql.rstrip().rstrip(";") + "\n; SELECT SCOPE_IDENTITY()"
        bound = tuple(params)
        if bound:
            self._cursor.execute(batch, bound)
        else:
            self._cursor.execute(batch)
        self._insert_rowcount = self._cursor.rowcount
        try:
            # Se positionner sur le jeu de résultats du SELECT : l'INSERT ne
            # produit qu'un compteur (description None), sauf si NOCOUNT est
            # actif (le lot s'ouvre alors directement sur le SELECT).
            while self._cursor.description is None:
                if not self._cursor.nextset():
                    break
            if self._cursor.description is not None:
                row = self._cursor.fetchone()
                if row and row[0] is not None:
                    self._lastrowid = int(row[0])
        except Exception:
            # Identité indéterminable (table sans colonne identity, pilote
            # sans nextset...) : l'INSERT est acquis, lastrowid reste None.
            self._lastrowid = None
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
        # Identité capturée dans le lot de l'INSERT (voir _execute_insert) ;
        # None si le dernier statement n'était pas un INSERT à identité.
        return self._lastrowid

    @property
    def rowcount(self) -> int:
        # Pour un INSERT batché, le rowcount vivant du curseur est celui du
        # SELECT SCOPE_IDENTITY() : on sert celui de l'INSERT, capturé avant.
        if self._insert_rowcount is not None:
            return self._insert_rowcount
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
        ("# Attente d'un verrou tenu par une autre transaction, avant un 503.", ""),
        ("DB_POOL_TIMEOUT", "5"),
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
        # Borne d'attente de verrou (DB-LOCK-WAIT-BOUND-001). Par défaut le
        # serveur fait patienter INDÉFINIMENT une écriture derrière un verrou
        # tenu (`LOCK_TIMEOUT` à -1) : une transaction coincée épuisait les
        # workers un à un, sans un 503 ni une ligne de journal. La borne est
        # `DB_POOL_TIMEOUT`, le temps qu'on accepte de patienter avant un 503.
        # Posée à chaque connexion : le pooling ODBC remet les options SET à
        # neuf entre deux réutilisations (`sp_reset_connection`). Le
        # dépassement rend l'erreur native 1222, qualifiée en indisponibilité
        # (DB-LOCK-TIMEOUT-QUALIFY-001). La connexion d'administration reste
        # sans borne, une migration a le droit d'attendre.
        lock_ms = max(1, int(float(os.environ.get("DB_POOL_TIMEOUT", "5")) * 1000))
        try:
            raw.execute(f"SET LOCK_TIMEOUT {lock_ms}")
        except BaseException:
            raw.close()
            raise
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

    def is_unique_violation(self, error: Exception) -> bool:
        """Doublon SQL Server : numéro natif 2627 (contrainte) ou 2601 (index).

        Le SQLSTATE ne convient pas : SQL Server renvoie `23000` aussi bien
        pour un doublon que pour une clé étrangère (erreur 547) ou un NOT NULL.
        pyodbc n'expose pas le numéro natif en attribut, il figure dans le
        message sous la forme « (2627) » ; on le cherche donc là, en restant
        strict (à défaut de numéro reconnu, ce n'est pas un doublon).
        """
        message = str(error)
        return "(2627)" in message or "(2601)" in message

    def is_unavailable(self, error: Exception) -> bool:
        """Indisponibilité SQL Server : connexion coupée, ou attente de verrou bornée.

        **La connexion coupée.** La classe SQLSTATE `08` est celle des
        « connection exception » de la norme, que le pilote ODBC respecte.
        Mesuré en tuant la session côté serveur, les deux requêtes suivantes
        rendent `08S01` (« Communication link failure »). pyodbc place le
        SQLSTATE en premier argument de l'exception ; c'est là qu'on le lit, la
        classe d'exception (`OperationalError`) étant trop large à elle seule.

        **Le verrou tenu trop longtemps.** L'erreur native 1222 (« Lock request
        time out period exceeded ») signale le dépassement d'une attente de
        verrou **bornée** (`SET LOCK_TIMEOUT`, posé par l'exploitant : SQL
        Server attend indéfiniment par défaut). Jumeau de l'errno 1205 de
        MariaDB, même critère, même famille : attendre suffit
        (DB-LOCK-TIMEOUT-QUALIFY-001). Le SQLSTATE ne peut pas servir seul,
        mesuré `42000`, la classe des erreurs de syntaxe : on exige donc le
        numéro natif dans le message, comme `is_unique_violation` avec 2627.
        L'interblocage (erreur native 1205 de SQL Server, victime désignée),
        lui, reste dehors : attendre n'y change rien.
        """
        args = getattr(error, "args", ())
        if not args or not isinstance(args[0], str):
            return False
        if args[0].startswith("08"):
            return True
        return args[0] == "42000" and "(1222)" in str(error)
