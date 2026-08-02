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

    def auto_increment_clause(self) -> str:
        """Mot-clé d'auto-incrément à ajouter après le type, ou chaîne vide.

        MariaDB sépare le type et l'auto-incrément (`BIGINT UNSIGNED` puis
        `AUTO_INCREMENT`). PostgreSQL et SQL Server portent l'auto-incrément
        **dans le type** (`BIGSERIAL`, `BIGINT IDENTITY(1,1)`) et renvoient
        donc une chaîne vide : ajouter un mot-clé y produirait du SQL invalide.

        Sert aux chemins qui composent une définition de colonne hors
        `CREATE TABLE`, typiquement un `ALTER TABLE ... ADD COLUMN` issu d'un
        diff. Pour la création de table, préférer `auto_increment_column_ddl()`,
        qui rend la ligne complète.
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

    def supports_transactional_ddl(self) -> bool:
        """Vrai si un `ROLLBACK` défait aussi la DDL déjà exécutée.

        Vérifié sur serveur réel avec une migration à deux `CREATE TABLE` dont
        le second est fautif :

            PostgreSQL   annule les deux            → vrai
            SQL Server   annule les deux            → vrai
            SQLite       annule les deux            → vrai
            MariaDB      garde la première table    → **faux**

        MariaDB valide implicitement avant et après chaque instruction de
        définition (`CREATE`, `ALTER`, `DROP`) : la transaction ouverte est
        close à son insu, et le `ROLLBACK` qui suit ne trouve plus rien à
        défaire. Ce n'est pas un défaut du pilote, c'est le moteur.

        Le moteur de migrations lit cette capacité pour dire la vérité quand
        une migration échoue en cours de route. Il ne **change pas** de
        stratégie selon la réponse : Forge ne peut pas rendre transactionnel ce
        qui ne l'est pas, et prétendre le contraire par un jeu de compensations
        écrites à l'aveugle serait exactement la magie que la charte refuse
        (principe 3). Il révèle l'état réellement atteint, à charge de
        l'opérateur de le rattraper (règle B).
        """
        ...

    def quote_identifier(self, name: str) -> str:
        """Échappe un identifiant SQL (backticks MariaDB, guillemets SQLite).

        Le délimiteur présent **dans** le nom doit être doublé, faute de quoi
        il referme la citation et la suite du nom devient de la syntaxe :
        ``a`b`` rendu ``` `a`b` ``` sort de la citation dès le deuxième
        caractère. Chaque dialecte double le sien : `` ` `` pour MariaDB,
        ``"`` pour SQLite et PostgreSQL, ``]`` pour SQL Server.

        Les identifiants que Forge produit sont contraints en amont
        (``^[a-z][a-z0-9_]*$`` dans les schémas JSON, `_IDENTIFIER_RE` dans
        `forge_mvc_entities.service`) et n'atteignent donc jamais ce cas. La
        méthode appartient malgré tout au contrat public, qui l'engage pour
        toute entrée (principe 10) : un appelant direct ne connaît pas cette
        contrainte amont.
        """
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
        (`SET FOREIGN_KEY_CHECKS` en MariaDB, `PRAGMA defer_foreign_keys` en
        SQLite, `session_replication_role` en PostgreSQL). Renvoie une liste
        vide si le dialecte n'expose pas de levier de session (SQL Server) : le
        chargement s'appuie alors sur le seul ordre topologique.

        Les instructions sont émises **dans** la transaction unique du
        chargement, ce qui exclut les leviers que le SGBD n'accepte qu'au
        dehors. C'est le cas de `PRAGMA foreign_keys`, sans effet une fois la
        transaction ouverte, d'où le report SQLite (SQLITE-FOREIGN-KEYS-ON-001).

        Le report n'est pas une désactivation : SQLite vérifie au `COMMIT` et
        refuse encore un enfant sans parent, là où MariaDB laisse tout passer.
        Un dialecte n'est pas tenu d'offrir la même force, seulement de dire ce
        qu'il offre.
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

    # ── Pagination (DML) ─────────────────────────────────────────────────────

    def pagination_clause(self) -> str:
        """Clause de pagination paramétrée, à placer **après** le `ORDER BY`.

        MariaDB, SQLite et PostgreSQL partagent `LIMIT ? OFFSET ?`. SQL Server
        n'a pas de `LIMIT` : il écrit `OFFSET ? ROWS FETCH NEXT ? ROWS ONLY`,
        forme qui **exige** un `ORDER BY` dans la requête.

        La clause porte toujours exactement deux marqueurs `?`, dont l'ordre
        n'est pas le même partout : le lire dans `pagination_param_order()`,
        jamais le supposer.
        """
        ...

    def limit_clause(self) -> str:
        """Clause bornant le nombre de lignes **sans décalage**, après le `ORDER BY`.

        MariaDB, SQLite et PostgreSQL écrivent `LIMIT ?`. SQL Server n'a pas de
        forme paramétrée équivalente en suffixe : il passe par
        `OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY`, qui exige un `ORDER BY`.

        Distincte de `pagination_clause()`, qui prend deux paramètres. Celle-ci
        n'en porte qu'un, donc aucun ordre à consulter.
        """
        ...

    def single_row_subquery(self, column: str, table: str, where: str) -> str:
        """Sous-requête scalaire bornée à **une** ligne, en SQL littéral.

        Distincte de `limit_clause()`, et pour deux raisons qui empêchent de la
        réutiliser. Celle-là est **paramétrée** (`LIMIT ?`), alors qu'on écrit
        ici du SQL destiné à un fichier, sans paramètre à lier. Et sa forme
        T-SQL, `OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY`, exige un `ORDER BY` et
        se place en suffixe, là où l'équivalent littéral naturel de SQL Server
        est `SELECT TOP 1`, en **tête** du `SELECT`.

        Aucun suffixe commun n'existe donc, et c'est pourquoi le dialecte rend
        la sous-requête entière plutôt qu'un morceau à recoller. Deux primitives
        à lire en paire auraient reproduit le piège de `pagination_clause()` et
        `pagination_param_order()`, dont l'ordre des marqueurs s'inverse en
        T-SQL.

            MariaDB, SQLite, PostgreSQL
                (SELECT Id FROM users WHERE Email = 'a@b.c' LIMIT 1)
            SQL Server
                (SELECT TOP 1 Id FROM users WHERE Email = 'a@b.c')

        `where` est une condition déjà rendue, littéraux compris : le dialecte
        n'en compose que l'enveloppe. Le premier appelant est `fixtures:generate`,
        dont les références écrivaient `LIMIT 1` en dur et ne chargeaient donc
        pas sur SQL Server (`FIXTURES-REFERENCE-DIALECT-001`).
        """
        ...

    # ── Horodatage serveur (DML) ─────────────────────────────────────────────

    def now_expression(self) -> str:
        """Expression SQL de l'instant courant, à insérer dans une requête.

        Les opt-ins adossés à la base écrivaient `NOW()`, qui n'existe ni en
        SQL Server ni en SQLite : mesuré, `jobs`, `notifications` et `settings`
        cassaient sur trois backends sur quatre alors que leur DDL, elle, était
        déjà dialectale (OPTIN-DML-DIALECT-001).

        La valeur rendue **coïncide avec celle de `timestamp_default_clause`**,
        et c'est la seule contrainte qui compte : une ligne insérée avec le
        défaut de la colonne et une ligne insérée avec cette expression doivent
        être comparables. MariaDB, PostgreSQL et SQLite rendent donc
        `CURRENT_TIMESTAMP`, SQL Server `SYSUTCDATETIME()`, exactement comme
        leurs clauses `DEFAULT`.

        Ce que cette méthode ne règle **pas** : une application qui a besoin
        d'un instant en Python le calcule en Python et le passe en paramètre,
        comme le fait `forge-mvc-sessions-db`. L'expression serveur ne sert que
        lorsque l'horloge de référence doit être celle du serveur.
        """
        ...

    def interval_seconds_expression(self, base: str) -> str:
        """Expression décalant `base` d'un nombre de secondes passé en paramètre.

        `base` est une expression SQL déjà rendue, typiquement
        `now_expression()`. L'expression retournée porte **exactement un**
        marqueur `?`, le nombre de secondes.

            MariaDB      {base} + INTERVAL ? SECOND
            PostgreSQL   {base} + (? * INTERVAL '1 second')
            SQL Server   DATEADD(second, ?, {base})
            SQLite       datetime({base}, '+' || ? || ' seconds')

        Aucune de ces quatre formes n'est acceptée par les trois autres : c'est
        la définition même d'un trait dialectal.
        """
        ...

    def pagination_param_order(self) -> "tuple[str, str]":
        """Ordre des deux paramètres de `pagination_clause()`.

        Rend `("limit", "offset")` pour la forme `LIMIT ? OFFSET ?`, et
        `("offset", "limit")` pour la forme T-SQL, qui annonce le décalage
        avant le nombre de lignes. Les deux méthodes vont par paire : une
        clause lue sans son ordre produit une pagination inversée, silencieuse
        et fausse.
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

    def is_unique_violation(self, error: Exception) -> bool:
        """Vrai si `error` signale une violation de contrainte d'unicité.

        La méthode est **sur le backend et non sur `Dialect`** : reconnaître
        une exception relève du pilote, là où `Dialect` ne décrit que du SQL.

        Aucun signal n'est portable, mesuré sur les quatre backends :

            MariaDB      mariadb.IntegrityError          errno 1062
            SQLite       sqlite3.IntegrityError          message « UNIQUE constraint failed »
            PostgreSQL   psycopg.errors.UniqueViolation  sqlstate 23505
            SQL Server   pyodbc.IntegrityError           numéro natif 2627

        Piège à ne pas reproduire : le SQLSTATE ne suffit pas. MariaDB **et**
        SQL Server renvoient `23000` aussi bien pour un doublon que pour un
        NOT NULL (MariaDB errno 1048) ou une clé étrangère. Une détection par
        SQLSTATE seul serait fausse sur la moitié des backends.

        L'implémentation doit être **stricte** : dans le doute, renvoyer faux.
        Un faux positif ferait passer une panne pour un doublon et afficherait
        une erreur de formulaire trompeuse à l'utilisateur.
        """
        ...

    def is_unavailable(self, error: Exception) -> bool:
        """Vrai si `error` dit « réessayez », non « votre requête est fautive ».

        La question porte sur une **famille**, pas sur une cause : le cœur fait
        la même chose de toutes ses réponses, un `DatabaseUnavailableError`,
        donc un **503 avec `Retry-After`**. La symétrie avec l'autre condition
        qualifiable est voulue, une question du contrat pour une erreur du cœur
        (`is_unique_violation` donne `UniqueViolationError`).

        Deux causes, de même nature du point de vue de l'appelant.

        **La connexion était morte.** Le serveur l'a fermée de son côté
        (``wait_timeout``, redémarrage, bascule) et le pilote la remet en
        circulation sans le savoir. Mesuré sur MariaDB, le pilote ne revalide
        qu'au delà d'une demi-seconde d'inactivité ; en deçà il livre la
        connexion morte, et l'exception du pilote traverse jusqu'à la page
        d'erreur.

        **La ressource était prise.** Sur un backend fichier, un seul écrivain
        est admis à la fois : le verrou tenu par un autre processus fait
        échouer l'écriture au bout du délai d'attente. C'est le jumeau exact de
        la saturation du pool sur un backend serveur, que le cœur qualifie déjà
        (`MARIADB-POOL-QUEUE-001`), et le remède est le même, attendre.

        Signaux relevés backend par backend, en tuant la connexion côté serveur
        ou en tenant le verrou depuis un second processus :

            MariaDB      mariadb.InterfaceError          errno 2006, 2013
            PostgreSQL   psycopg.OperationalError        sqlstate 57P01 puis aucun
            SQL Server   pyodbc.OperationalError         sqlstate 08S01
            SQLite       sqlite3.OperationalError        SQLITE_BUSY, SQLITE_LOCKED

        Comme pour `is_unique_violation`, aucun signal n'est portable et la
        méthode appartient au backend, seul à connaître son pilote. Un backend
        n'est pas tenu de reconnaître les deux causes, seulement de dire
        lesquelles il reconnaît : SQLite n'a pas de connexion à perdre, les
        trois backends serveur n'ont pas de verrou de fichier.

        Forge ne rejoue **pas** la requête à la place de l'appelant : réémettre
        en silence une écriture dont on ignore si le serveur l'a reçue serait
        de la magie cachée (principe 3).

        Même exigence de stricte : dans le doute, renvoyer faux. Un faux
        positif masquerait une vraie panne derrière une invitation à réessayer.
        """
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
