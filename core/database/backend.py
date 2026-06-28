# pyright: strict
"""
core/database/backend.py — Contrat de backend BDD et résolveur (ADR-054)
========================================================================
Le cœur de Forge est agnostique BDD : il ne connaît pas de SGBD particulier,
il connaît un *contrat* de backend. Chaque SGBD est fourni par un opt-in
(`forge-mvc-mariadb`, `forge-mvc-sqlite`, ...) qui implémente ce contrat et
s'enregistre via un entry point de packaging, dans le groupe
``forge_mvc.db_backend``.

    [project.entry-points."forge_mvc.db_backend"]
    mariadb = "forge_mvc_mariadb.backend:MariaDBBackend"

Le résolveur découvre le backend installé sans configuration : l'application
« voit » l'opt-in et se câble dessus. Règles (ADR-054) :

- un seul backend autorisé par projet (exclusivité mutuelle) ;
- aucun backend installé → erreur explicite (le cœur n'a aucune prise en charge
  BDD par lui-même : il faut installer un opt-in, par exemple forge-mvc-mariadb) ;
- la variable d'environnement ``DB_BACKEND`` tranche un cas ambigu en nommant
  explicitement le backend voulu (par son nom d'entry point).

Un backend doit fournir des connexions compatibles avec l'API d'exécution du
cœur (`core.database.db`) : objets exposant ``cursor(dictionary=...)``,
``commit()``, ``rollback()``, ``close()``, l'attribut ``autocommit`` et, sur le
curseur, ``execute``, ``fetchone``, ``fetchall``, ``lastrowid``, ``rowcount``.
"""
import logging
import os
import threading
from importlib.metadata import entry_points
from typing import Any, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

ENTRY_POINT_GROUP = "forge_mvc.db_backend"
ENV_OVERRIDE = "DB_BACKEND"


@runtime_checkable
class Dialect(Protocol):
    """Traits SQL propres à un SGBD, consommés par les générateurs (ADR-054).

    Couvre pour l'instant le mapping des types Forge vers les types de colonne
    SQL (le seul concern dialectal déjà câblé). Les autres traits (quoting des
    identifiants, mot-clé d'auto-incrément, introspection, provisioning) seront
    ajoutés au fil des tickets DDL.
    """

    def string_type(self, max_length: int) -> str:
        """Type colonne pour `string` (longueur validée par l'appelant)."""
        ...

    def decimal_type(self, precision: int, scale: int) -> str:
        """Type colonne pour `decimal` (precision/scale validés par l'appelant)."""
        ...

    def simple_type(self, forge_type: str) -> str:
        """Type colonne pour un type Forge simple (text, integer, boolean, ...)."""
        ...

    def identity_type(self) -> str:
        """Type colonne de la clé primaire auto-incrémentée `id`."""
        ...

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        """Types Python compatibles avec ce type de colonne, dans ce dialecte.

        Sert à valider la cohérence sql_type / python_type d'une entité. En
        MariaDB chaque type a une famille (ex. DATETIME -> datetime) ; en SQLite
        une affinité en couvre plusieurs (ex. TEXT -> str, date, datetime).
        Tuple vide si le type est inconnu.
        """
        ...

    # ── DDL (CREATE TABLE) ───────────────────────────────────────────────────

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        """Définition complète de la colonne PK auto-incrémentée.

        MariaDB : « col TYPE NOT NULL AUTO_INCREMENT » (+ clause PRIMARY KEY
        séparée). SQLite : « col INTEGER PRIMARY KEY AUTOINCREMENT » (PK inline).
        """
        ...

    def emits_separate_primary_key(self) -> bool:
        """Vrai si la PK s'exprime par une clause `PRIMARY KEY (col)` séparée.

        Faux pour SQLite, qui porte la PK auto-incrémentée sur la colonne.
        """
        ...

    def unique_is_column_constraint(self) -> bool:
        """Vrai si l'unicité s'exprime sur la colonne (« col TYPE ... UNIQUE »).

        SQLite l'exige (les contraintes de table doivent suivre toutes les
        colonnes) ; MariaDB émet une ligne `UNIQUE KEY ...` séparée (faux).
        """
        ...

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        """Ligne de contrainte d'unicité de table (si non portée par la colonne)."""
        ...

    def table_suffix(self) -> str:
        """Suffixe après la parenthèse fermante (moteur, charset...) ou « »."""
        ...

    def forge_migrations_ddl(self) -> str:
        """DDL de la table technique `forge_migrations`, propre au dialecte."""
        ...

    def quote_identifier(self, name: str) -> str:
        """Échappe un identifiant SQL (backticks MariaDB, guillemets SQLite)."""
        ...

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        """Migration d'ajout de colonnes. `columns` : (nom, définition SQL).

        MariaDB : un seul ALTER TABLE avec plusieurs ADD COLUMN. SQLite : un
        ALTER TABLE par colonne (un seul ADD COLUMN par instruction).
        """
        ...

    def introspect_columns(
        self, connection: Any, table: str, database: str
    ) -> "list[tuple[str, str, bool, bool]]":
        """Colonnes existantes de `table` : (nom, type_sql, nullable, auto_increment).

        L'introspection est propre au SGBD (INFORMATION_SCHEMA en MariaDB,
        PRAGMA en SQLite). `database` est utilisé par les SGBD serveur ; ignoré
        par les backends fichier.
        """
        ...


@runtime_checkable
class DatabaseBackend(Protocol):
    """Contrat qu'un opt-in de backend BDD doit implémenter."""

    name: str
    dialect: Dialect
    # Vrai pour un SGBD serveur à provisionner (base + comptes via db:init,
    # ex. MariaDB) ; faux pour un backend fichier sans comptes (ex. SQLite).
    requires_provisioning: bool

    def get_connection(self) -> Any:
        """Fournit une connexion prête à l'emploi (pool ou directe)."""
        ...

    def close_connection(self, connection: Any) -> None:
        """Restitue/ferme la connexion empruntée."""
        ...


_backend: "DatabaseBackend | None" = None
_lock = threading.Lock()


def _no_backend_error() -> "RuntimeError":
    return RuntimeError(
        "Aucun backend BDD installé. Le cœur de Forge est agnostique BDD "
        "(ADR-054) : installez un opt-in de backend, par exemple "
        "`pip install forge-mvc-mariadb`."
    )


def _discover() -> "DatabaseBackend":
    discovered = list(entry_points(group=ENTRY_POINT_GROUP))

    requested = os.environ.get(ENV_OVERRIDE)
    if requested:
        matches = [ep for ep in discovered if ep.name == requested]
        if not matches:
            available = ", ".join(sorted(ep.name for ep in discovered)) or "aucun"
            raise RuntimeError(
                f"Backend BDD demandé introuvable : {requested!r} "
                f"(DB_BACKEND). Backends installés : {available}."
            )
        return matches[0].load()()

    if len(discovered) > 1:
        names = ", ".join(sorted(ep.name for ep in discovered))
        raise RuntimeError(
            f"Plusieurs backends BDD installés ({names}). Un seul est autorisé "
            "par projet (ADR-054). Désinstallez les opt-ins en trop ou fixez "
            "DB_BACKEND."
        )

    if len(discovered) == 1:
        backend = discovered[0].load()()
        logger.debug("Backend BDD résolu via entry point : %s", discovered[0].name)
        return backend

    raise _no_backend_error()


def get_backend() -> "DatabaseBackend":
    """Retourne le backend BDD actif (résolu une fois, mémorisé)."""
    global _backend
    if _backend is None:
        with _lock:
            if _backend is None:
                _backend = _discover()
    return _backend


def reset_backend() -> None:
    """Réinitialise le backend résolu.

    Ferme proprement le backend courant s'il expose ``close()`` (libération
    du pool), puis force une nouvelle résolution au prochain ``get_backend()``.
    Utilisé en fin de session de test.
    """
    global _backend
    with _lock:
        if _backend is not None:
            close = getattr(_backend, "close", None)
            if callable(close):
                close()
        _backend = None
