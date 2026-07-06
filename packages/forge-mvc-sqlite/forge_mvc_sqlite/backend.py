# pyright: strict
"""
forge_mvc_sqlite.backend — Backend BDD SQLite pour Forge (ADR-054)
==================================================================
Implémente le contrat `core.database.backend.DatabaseBackend` au-dessus du
module `sqlite3` de la bibliothèque standard. Aucune dépendance externe, aucun
serveur : la base est un fichier (chemin = `DB_NAME`).

Le cœur attend des connexions compatibles DB-API « à la MariaDB » :
``cursor(dictionary=...)``, ``commit``/``rollback``/``close``, l'attribut
``autocommit``, et sur le curseur ``execute``/``fetchone``/``fetchall``/
``lastrowid``/``rowcount``. `sqlite3` ne fournit pas le mode « lignes-dict » ni
le mot-clé ``dictionary`` : ce module l'adapte via de fines enveloppes.

Une connexion neuve est ouverte à chaque emprunt (SQLite est léger ; pas de
pool). Les requêtes générées par Forge utilisent déjà des paramètres ``?``,
nativement supportés par SQLite.
"""
import os
import sqlite3
from typing import Any

from forge_mvc_sqlite.dialect import SQLiteDialect


class _SQLiteCursor:
    """Enveloppe d'un curseur sqlite3 : ajoute le mode lignes-dict."""

    def __init__(self, cursor: sqlite3.Cursor, dictionary: bool) -> None:
        self._cursor = cursor
        self._dictionary = dictionary

    def execute(self, sql: str, params: "Any" = ()) -> "_SQLiteCursor":
        self._cursor.execute(sql, tuple(params))
        return self

    @property
    def lastrowid(self) -> "int | None":
        return self._cursor.lastrowid

    @property
    def rowcount(self) -> int:
        return self._cursor.rowcount

    def _columns(self) -> list[str]:
        return [d[0] for d in (self._cursor.description or [])]

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
            cols = self._columns()
            return [dict(zip(cols, r)) for r in rows]
        return rows

    def close(self) -> None:
        self._cursor.close()


class _SQLiteConnection:
    """Enveloppe d'une connexion sqlite3 conforme aux attentes du cœur."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def cursor(self, *, dictionary: bool = False) -> _SQLiteCursor:
        return _SQLiteCursor(self._connection.cursor(), dictionary)

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


class SQLiteBackend:
    """Backend BDD SQLite : une connexion par emprunt (fichier `DB_NAME`)."""

    name = "sqlite"
    dialect = SQLiteDialect()
    requires_provisioning = False
    # Variable d'environnement lue par le backend (ADR-064) : le chemin du
    # fichier de base. Amorcée par `forge db:config`. Sans serveur ni comptes.
    env_template: "list[tuple[str, str]]" = [
        ("# Chemin du fichier de base SQLite, relatif à la racine du projet (sans serveur ni comptes).", ""),
        ("DB_NAME", "storage/app.db"),
    ]

    def get_connection(self) -> Any:
        """Ouvre une connexion SQLite sur le fichier configuré (`DB_NAME`).

        ADR-060 : le chemin du fichier est lu dans l'environnement (DB_NAME).
        """
        database = os.environ.get("DB_NAME", "")
        raw = sqlite3.connect(database, check_same_thread=False)
        return _SQLiteConnection(raw)

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        """SQLite est sans serveur : aucune connexion d'administration.

        Ce chemin n'est jamais emprunté (`requires_provisioning=False` aiguille
        la CLI vers la voie « serverless »).
        """
        raise RuntimeError(
            "Le backend SQLite est sans serveur : pas de connexion "
            "d'administration (requires_provisioning=False)."
        )

    def close_connection(self, connection: Any) -> None:
        """Ferme la connexion empruntée."""
        if connection is not None:
            connection.close()
