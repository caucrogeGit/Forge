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

    def identity_storage_type(self) -> str:
        """Type colonne pour **stocker** une valeur d'identité (clé étrangère).

        À ne pas confondre avec `identity_type()`, qui décrit la forme DDL
        d'une colonne **auto-incrémentée** (la clé primaire). Les deux
        coïncident sur MariaDB (`BIGINT UNSIGNED`) et SQLite (`INTEGER`), mais
        pas sur PostgreSQL (`BIGINT` contre `BIGSERIAL`) ni SQL Server
        (`BIGINT` contre `BIGINT IDENTITY(1,1)`).

        Employer `identity_type()` pour une clé étrangère y attacherait une
        séquence ou une propriété IDENTITY : la colonne référençante se verrait
        attribuer une valeur toute seule (FK-IDENTITY-STORAGE-TYPE-001).
        """
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

    def create_table_opening(self, table: str) -> str:
        """Début d'un CREATE TABLE idempotent, jusqu'avant la parenthèse.

        MariaDB/SQLite/PostgreSQL : `CREATE TABLE IF NOT EXISTS {table}`.
        SQL Server n'a pas IF NOT EXISTS : forme gardée `IF OBJECT_ID(...) IS
        NULL CREATE TABLE {table}`.
        """
        ...

    def forge_migrations_ddl(self) -> str:
        """DDL de la table technique `forge_migrations`, propre au dialecte."""
        ...

    def quote_identifier(self, name: str) -> str:
        """Échappe un identifiant SQL (backticks MariaDB, guillemets SQLite)."""
        ...

    # ── DML (rendu de littéraux, ADR-075) ────────────────────────────────────

    def render_literal(self, value: object) -> str:
        """Rend une valeur Python comme littéral SQL de ce dialecte (ADR-075).

        Couvre None, bool, int, float, Decimal, str, date, datetime ; lève sur
        un type non couvert. Booléens et dates sont propres au dialecte (`1`/`0`
        contre `TRUE`/`FALSE`, formes de date), chaînes échappées (`''`, `N'...'`
        en SQL Server).

        Réservé à la **génération d'artefacts relus** (fixtures, `DEFAULT` de
        DDL) : le littéral est du SQL visible. Ne JAMAIS l'utiliser pour une
        requête à l'exécution (la DML reste paramétrée, principe 7).
        """
        ...

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        """Migration d'ajout de colonnes. `columns` : (nom, définition SQL).

        MariaDB : un seul ALTER TABLE avec plusieurs ADD COLUMN. SQLite : un
        ALTER TABLE par colonne (un seul ADD COLUMN par instruction).
        """
        ...

    def named_unique(self, name: str, columns: "list[str]") -> str:
        """Contrainte d'unicité de table (composite possible), en ligne.

        MariaDB : `UNIQUE KEY {name} (...)` ; SQLite : `UNIQUE (...)` (sans nom).
        """
        ...

    def inline_indexes(self) -> bool:
        """Vrai si les index se déclarent dans le CREATE TABLE (MariaDB).

        Faux pour SQLite, qui exige des instructions CREATE INDEX séparées.
        """
        ...

    def index_clause(self, name: str, column: str) -> str:
        """Clause d'index en ligne dans le CREATE TABLE (si inline_indexes)."""
        ...

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        """Instruction CREATE INDEX autonome (si index non inline)."""
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

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        """Instructions SQL pour (dés)activer la vérification des clés étrangères.

        Utilisé par `fixtures:load --no-fk-checks` (ADR-077) pour charger un jeu
        non triable (cycle de dépendances FK) sans violer les contraintes :
        désactivation avant le chargement, réactivation après. Propre au SGBD
        (`SET FOREIGN_KEY_CHECKS` en MariaDB, `PRAGMA foreign_keys` en SQLite,
        `session_replication_role` en PostgreSQL). Renvoie une liste vide si le
        dialecte n'expose pas de levier de session (SQL Server) : le chargement
        s'appuie alors sur le seul ordre topologique.
        """
        ...

    # ── DDL du socle Auth/User (ADR-084) ─────────────────────────────────────

    def auto_increment_primary_key_ddl(self, column: str, sql_type: str) -> str:
        """Définition d'une colonne PK auto-incrémentée avec PRIMARY KEY inline.

        Contrairement à `auto_increment_column_ddl` (entités, PK en clause
        séparée possible), cette forme porte toujours PRIMARY KEY sur la
        colonne : c'est le style canonique du socle Auth/User (ADR-084).
        MariaDB : « col INT AUTO_INCREMENT PRIMARY KEY » ; SQLite :
        « col INTEGER PRIMARY KEY AUTOINCREMENT » (type imposé INTEGER) ;
        PostgreSQL : « col SERIAL PRIMARY KEY » ; SQL Server :
        « col INT IDENTITY(1,1) PRIMARY KEY ».
        """
        ...

    def char_type(self, length: int) -> str:
        """Type colonne pour une chaîne de longueur fixe (hash hexadécimal...).

        MariaDB/PostgreSQL/SQL Server : `CHAR(n)` ; SQLite : `TEXT` (affinité,
        pas de longueur).
        """
        ...

    def boolean_default_literal(self, value: bool) -> str:
        """Littéral booléen d'une clause DEFAULT de DDL.

        Distinct de `render_literal` (ADR-075, artefacts DML) : ici le littéral
        qualifie une colonne booléenne dans un CREATE TABLE. MariaDB et
        PostgreSQL écrivent `TRUE`/`FALSE` ; SQLite (INTEGER) et SQL Server
        (BIT) écrivent `1`/`0`.
        """
        ...

    def timestamp_default_clause(self, *, on_update: bool) -> str:
        """Clause DEFAULT d'une colonne d'horodatage, avec ou sans on-update.

        MariaDB : `DEFAULT CURRENT_TIMESTAMP` et, si `on_update`, ajoute
        `ON UPDATE CURRENT_TIMESTAMP`. SQLite et PostgreSQL n'ont pas
        d'équivalent déclaratif de l'on-update : la clause reste
        `DEFAULT CURRENT_TIMESTAMP` et la mise à jour de la colonne est à la
        charge de l'application (ou d'un trigger). SQL Server utilise
        `DEFAULT SYSUTCDATETIME()` (cohérent avec `forge_migrations_ddl`).
        """
        ...

    def collated_table_suffix(self) -> str:
        """Suffixe de table avec collation explicite, ou chaîne vide.

        MariaDB : « ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
        COLLATE=utf8mb4_unicode_ci » (forme historique du socle Auth/User et de
        `forge_migrations_ddl`, plus complète que `table_suffix`). Les autres
        dialectes n'ont pas d'options de table : chaîne vide.
        """
        ...

    # ── DDL des relations many_to_one (ADR-084) ──────────────────────────────

    def add_foreign_key_sql(
        self,
        *,
        table: str,
        column: str,
        sql_type: str,
        nullable: bool,
        ref_table: str,
        ref_column: str,
        constraint_name: str,
        on_delete: str,
        on_update: str,
        index_name: "str | None",
        add_column: bool,
    ) -> "list[str]":
        """Énoncés SQL posant une clé étrangère `many_to_one` sur une table existante.

        `add_column` est vrai quand la colonne FK n'est pas déclarée comme champ
        d'entité : la colonne est alors créée (type `sql_type`, nullabilité
        `nullable`) avant la contrainte. `index_name` demande un index sur la
        colonne (None : pas d'index). MariaDB, PostgreSQL et SQL Server émettent
        ALTER TABLE ADD COLUMN (ADD seul en T-SQL), ALTER TABLE ADD CONSTRAINT
        puis CREATE INDEX. SQLite ne supporte pas ALTER TABLE ADD CONSTRAINT :
        quand la colonne est créée, la contrainte est portée inline par
        ADD COLUMN (clause REFERENCES) ; quand la colonne existe déjà, le
        dialecte émet un commentaire SQL explicite plutôt qu'un énoncé
        inapplicable (règle B, ADR-084).
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
    # Variables d'environnement lues par le backend, dans l'ordre, chacune avec
    # une valeur d'exemple ou un placeholder vide (ADR-064). `forge db:config`
    # s'en sert pour amorcer env/example, env/dev et env/prod. Aucune valeur
    # sensible ici : uniquement des exemples (hôte, port) ou du vide.
    # Une entrée dont la clé commence par « # » est une ligne de commentaire,
    # rendue verbatim dans le bloc pour documenter les variables (sa valeur est
    # ignorée) ; elle n'est ni détectée comme clé présente ni renseignée.
    env_template: "list[tuple[str, str]]"

    def get_connection(self) -> Any:
        """Fournit une connexion prête à l'emploi (pool ou directe)."""
        ...

    def get_admin_connection(self, *, database: "str | None" = None) -> Any:
        """Connexion d'administration pour la DDL et le provisioning.

        Le backend lit lui-même sa configuration dans l'environnement : serveur
        partagé `DB_HOST`/`DB_PORT` et identifiants d'administration
        `DB_ADMIN_LOGIN`/`DB_ADMIN_PWD` (ADR-060, ADR-066). `database=None`
        cible la base de maintenance du serveur (provisioning via `db:init`) ; un
        nom cible la base du projet (`db:apply`, migrations). Réservée aux SGBD
        serveur ; un backend sans serveur (`requires_provisioning=False`) lève une
        erreur car il n'a pas de compte d'administration.
        """
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
