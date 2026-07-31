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
from pathlib import Path
from typing import Any

from core.database.errors import DatabaseConfigurationError
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
        ("# Attente devant un fichier verrouillé par un autre écrivain, avant un 503.", ""),
        ("DB_POOL_TIMEOUT", "5"),
    ]

    def get_connection(self) -> Any:
        """Ouvre une connexion SQLite sur le fichier configuré (`DB_NAME`).

        ADR-060 : le chemin du fichier est lu dans l'environnement (DB_NAME).

        Les clés étrangères sont **armées à chaque emprunt**. SQLite les laisse
        inactives par défaut, par compatibilité ascendante, et le réglage est
        propre à la connexion : sans ce pragma, les contraintes que
        `make:relation` écrit dans la DDL ne contraignaient rien. Mesuré, un
        enfant orphelin passait et `ON DELETE CASCADE` ne cascadait pas, là où
        les trois autres backends refusaient ou cascadaient
        (SQLITE-FOREIGN-KEYS-ON-001).

        Le sens de la dérive commandait de corriger : SQLite sert en
        développement, les SGBD serveur en production. Un défaut d'intégrité ne
        se voyait donc jamais chez le développeur, toujours chez l'utilisateur,
        et sur des données déjà incohérentes.

        L'ordre compte, et il est vérifié : le pragma est sans effet dans une
        transaction ouverte. Armé ici, à l'emprunt, il survit au désarmement
        d'autocommit que `core.database.transaction` opère juste après.

        Le temps d'attente devant un fichier verrouillé est lu dans
        ``DB_POOL_TIMEOUT``, la variable que MariaDB emploie déjà pour attendre
        devant un pool saturé. Les deux nomment la même chose, le temps qu'on
        accepte de patienter avant de rendre un 503, et une seule façon
        officielle vaut mieux que deux (principe 11). Sans elle, `sqlite3`
        applique cinq secondes en dur, que rien ne permettait d'ajuster.

        La connexion d'exécution **n'a pas le droit de créer le fichier**
        (SQLITE-RUNTIME-NO-CREATE-001). Ouverte en création, elle fabriquait une
        base vide dès que `DB_NAME` désignait un fichier absent, une faute de
        frappe suffisant : l'application démarrait, puis annonçait « table
        inconnue » page après page, là où la vérité était « base absente ».
        Créer une base à l'insu de l'exploitant est l'écriture invisible que la
        charte refuse. La création appartient au provisionnement.
        """
        return _SQLiteConnection(self._connect(create=False))

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        """Connexion de provisionnement : la seule autorisée à créer le fichier.

        SQLite n'a pas de compte d'administration, `requires_provisioning` reste
        donc faux et la CLI ne lui demande ni base ni comptes à créer. Le
        **rôle**, lui, existe bel et bien : le contrat le définit comme celui de
        la DDL et du provisionnement (ADR-033), et pour un backend fichier cela
        se traduit par un privilège précis, celui de créer le fichier.

        C'est `forge db:init` qui l'emprunte, une fois, pour préparer la base et
        la table `forge_migrations`. L'exécution passe par `get_connection`, qui
        refuse de créer quoi que ce soit (SQLITE-RUNTIME-NO-CREATE-001).

        `database` nomme un autre fichier que `DB_NAME` si besoin ; les
        identifiants `DB_ADMIN_*` n'ont ici aucun sens et ne sont pas lus.
        """
        return _SQLiteConnection(self._connect(create=True, database=database))

    def _connect(self, *, create: bool, database: "str | None" = None) -> sqlite3.Connection:
        """Ouvre le fichier, avec ou sans droit de création, et arme les FK.

        Le refus de création passe par l'URI `mode=rw`, seule forme que
        `sqlite3` accepte pour cela. Le chemin est résolu en absolu avant d'y
        entrer, ce qui règle du même coup la question du répertoire de
        lancement : un `DB_NAME` relatif dépend de l'endroit d'où le serveur a
        été démarré, et le message d'erreur nomme désormais le chemin réellement
        tenté plutôt que de laisser deviner.
        """
        name = database if database is not None else os.environ.get("DB_NAME", "")
        timeout = float(os.environ.get("DB_POOL_TIMEOUT", "5"))
        if not name:
            raise DatabaseConfigurationError(
                "DB_NAME n'est pas défini : le backend SQLite ne sait pas quel "
                "fichier ouvrir. Renseignez-le dans env/dev (voir `forge db:config`)."
            )
        if name == ":memory:":
            # Base en mémoire, explicitement demandée : rien à créer ni à
            # trouver sur disque, la question du droit de création ne se pose pas.
            raw = sqlite3.connect(name, timeout=timeout, check_same_thread=False)
            raw.execute("PRAGMA foreign_keys = ON")
            return raw

        path = Path(name).resolve()
        if create:
            raw = sqlite3.connect(str(path), timeout=timeout, check_same_thread=False)
        else:
            try:
                raw = sqlite3.connect(f"{path.as_uri()}?mode=rw", uri=True,
                                      timeout=timeout, check_same_thread=False)
            except sqlite3.OperationalError as error:
                if path.exists():
                    # Le fichier est là mais illisible : droits, disque,
                    # corruption. Panne durable, dont le message du pilote dit
                    # déjà la nature ; l'envelopper la masquerait.
                    raise
                raise DatabaseConfigurationError(
                    f"Aucune base SQLite à l'emplacement « {path} » "
                    f"(DB_NAME = {name!r}).\n"
                    "Forge ne crée pas de base au vol : une base vide ferait "
                    "répondre « table inconnue » à chaque page.\n"
                    "Lancez `forge db:init` pour la créer, ou corrigez DB_NAME "
                    "dans env/dev."
                ) from error
        raw.execute("PRAGMA foreign_keys = ON")
        return raw

    def close_connection(self, connection: Any) -> None:
        """Ferme la connexion empruntée."""
        if connection is not None:
            connection.close()

    def is_unique_violation(self, error: Exception) -> bool:
        """Doublon SQLite : `sqlite3.IntegrityError` au message explicite.

        SQLite n'expose ni SQLSTATE ni code d'erreur distinct sur l'exception ;
        le message est le seul signal. Il est stable et documenté :
        « UNIQUE constraint failed: table.colonne ». Les autres violations ont
        leur propre libellé (« NOT NULL constraint failed », « FOREIGN KEY
        constraint failed »), donc la discrimination reste sûre.
        """
        import sqlite3

        if not isinstance(error, sqlite3.IntegrityError):
            return False
        return "UNIQUE constraint failed" in str(error)

    def is_unavailable(self, error: Exception) -> bool:
        """Indisponibilité SQLite : le fichier est verrouillé par un autre écrivain.

        SQLite n'a pas de connexion à perdre, le fichier étant ouvert par le
        processus lui-même. Il a en revanche l'autre cause de la famille, et
        sous une forme plus stricte que les SGBD serveur : **un seul écrivain à
        la fois**. Une sauvegarde, un `fixtures:load` ou un second processus qui
        tient une transaction fait attendre l'écriture, puis échouer au delà du
        délai. La condition est passagère, l'écrivain d'à côté finira, et
        réessayer suffit : c'est le jumeau exact de la saturation du pool sur un
        backend serveur (SQLITE-BUSY-503-001).

        La discrimination se fait sur le **code** de SQLite, exposé par
        `sqlite3` depuis Python 3.11, et non sur le message : `SQLITE_BUSY`
        quand le verrou est tenu ailleurs, `SQLITE_LOCKED` quand il l'est dans
        la même connexion. C'est plus solide que ce que peuvent faire les trois
        autres backends, dont les pilotes n'exposent pas toujours de code.

        Un échec de disque ou de permission, lui, reste durable : il n'entre pas
        dans la famille et appelle bien un 500.
        """
        import sqlite3

        if not isinstance(error, sqlite3.OperationalError):
            return False
        nom = getattr(error, "sqlite_errorname", "")
        return isinstance(nom, str) and nom.startswith(("SQLITE_BUSY", "SQLITE_LOCKED"))
