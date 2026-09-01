# pyright: strict
"""
forge_mvc_sqlite.dialect — Traits SQL SQLite (ADR-054)
======================================================
Mapping des types Forge vers les affinités de colonne SQLite. SQLite a un
typage par affinité (TEXT, INTEGER, REAL, NUMERIC) : pas de longueur, pas de
type booléen ni date/heure natifs (stockés en TEXT ISO ou entier 0/1).
"""
import re
from typing import Any

from core.database.literals import escape_string, render_literal_value

_SAFE_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


def _is_rowid_alias(row: Any) -> bool:
    """Vrai si la colonne est un `INTEGER PRIMARY KEY`, alias du rowid.

    C'est la seule colonne que SQLite auto-incrémente, et la seule dont il
    refuse les NULL sans le déclarer dans `PRAGMA table_info`.
    """
    return bool(row[5]) and str(row[2]).upper() == "INTEGER"


# Types Forge « simples » → affinité SQLite.
_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INTEGER",
    "big_integer": "INTEGER",
    "float":       "REAL",
    "boolean":     "INTEGER",
    "date":        "TEXT",
    "datetime":    "TEXT",
    "email":       "TEXT",
    "password":    "TEXT",
    "slug":        "TEXT",
    "json":        "TEXT",
}


class SQLiteDialect:
    """Traits SQL de SQLite (typage par affinité)."""

    def string_type(self, max_length: int) -> str:
        # SQLite ignore la longueur (affinité TEXT).
        return "TEXT"

    def decimal_type(self, precision: int, scale: int) -> str:
        return "NUMERIC"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        # La clé primaire auto-incrémentée SQLite doit être de type INTEGER.
        return "INTEGER"

    def identity_storage_type(self) -> str:
        # SQLite : AUTOINCREMENT est une clause à part, portée par la colonne
        # PK. INTEGER est déjà un type de stockage ordinaire.
        return "INTEGER"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        # Affinités SQLite : une même affinité couvre plusieurs familles Python
        # (TEXT stocke aussi dates et JSON ; INTEGER stocke aussi les booléens).
        n = sql_type.strip().upper()
        if n == "INTEGER":
            return ("int", "bool")
        if n == "REAL":
            return ("float",)
        if n == "NUMERIC":
            return ("float",)
        if n == "TEXT":
            return ("str", "date", "datetime")
        return ()

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        # SQLite : la PK auto-incrémentée est portée par la colonne elle-même.
        return f"{column} {sql_type} PRIMARY KEY AUTOINCREMENT"

    def auto_increment_clause(self) -> str:
        # SQLite ne sait pas ajouter une colonne AUTOINCREMENT par ALTER TABLE :
        # aucun mot-cle utilisable hors CREATE TABLE.
        return ""

    def emits_separate_primary_key(self) -> bool:
        return False

    def unique_is_column_constraint(self) -> bool:
        # SQLite : l'unicité est portée par la colonne (contraintes de table
        # après toutes les colonnes seulement) — voir build_entity_sql.
        return True

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        return f"UNIQUE ({column})"

    def table_suffix(self) -> str:
        return ""

    def create_table_opening(self, table: str) -> str:
        return f"CREATE TABLE IF NOT EXISTS {table}"

    def forge_migrations_ddl(self) -> str:
        return (
            "CREATE TABLE IF NOT EXISTS forge_migrations (\n"
            "    id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
            "    version TEXT NOT NULL,\n"
            "    name TEXT NOT NULL,\n"
            "    filename TEXT NOT NULL,\n"
            "    checksum TEXT NOT NULL,\n"
            "    applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "    execution_ms INTEGER,\n"
            "    UNIQUE (version),\n"
            "    UNIQUE (filename)\n"
            ")"
        )

    def supports_transactional_ddl(self) -> bool:
        """Vrai : SQLite journalise la DDL comme le reste, le rollback la défait."""
        return True

    def quote_identifier(self, name: str) -> str:
        # Le guillemet contenu dans le nom se double, sans quoi il referme la
        # citation et la suite du nom devient de la syntaxe.
        return '"' + name.replace('"', '""') + '"'

    def render_literal(self, value: object) -> str:
        # SQLite : pas de booléen ni de date natifs (0/1 et chaîne ISO), ADR-075.
        return render_literal_value(
            value,
            bool_true="1",
            bool_false="0",
            render_string=escape_string,
            render_date=lambda d: escape_string(d.isoformat()),
            render_datetime=lambda dt: escape_string(dt.strftime("%Y-%m-%d %H:%M:%S")),
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        # SQLite : une seule colonne ajoutée par ALTER TABLE.
        return "".join(
            f"ALTER TABLE {self.quote_identifier(table)} "
            f"ADD COLUMN {self.quote_identifier(name)} {definition};\n"
            for name, definition in columns
        )

    def named_unique(self, name: str, columns: "list[str]") -> str:
        # SQLite : contrainte d'unicité sans nom (les noms d'index se déclarent
        # via CREATE INDEX/UNIQUE INDEX séparés).
        return f"UNIQUE ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return False

    def index_clause(self, name: str, column: str) -> str:
        # Non utilisé en SQLite (index hors CREATE TABLE) ; fourni pour le contrat.
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        return f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column});"

    def server_diagnostics_sql(self) -> "dict[str, str]":
        # SQLite est un fichier, sans serveur ni compte : seules la version du
        # moteur et l'encodage du fichier ont un sens.
        return {
            "version": "SELECT sqlite_version() AS value",
            "encodage": "SELECT * FROM pragma_encoding() AS value",
        }

    def unique_nullable_index_sql(self, table: str, name: str, column: str) -> str:
        # SQLite accepte plusieurs NULL dans un index unique.
        return f"CREATE UNIQUE INDEX IF NOT EXISTS {name} ON {table} ({column});"

    def add_column_clause(self, table: str, definition: str) -> str:
        return f"ALTER TABLE {table} ADD COLUMN {definition};"

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        """Report des contraintes, seul levier utilisable là où il sert (ADR-077).

        `fixtures:load --no-fk-checks` émet ces instructions **dans** la
        transaction unique du chargement, et `PRAGMA foreign_keys` y est sans
        effet : SQLite ne l'accepte que hors transaction. Tant que les
        contraintes n'étaient pas armées, cela ne se voyait pas, l'ordre
        n'ayant rien à désactiver ; armées (SQLITE-FOREIGN-KEYS-ON-001), il
        aurait menti en silence.

        `defer_foreign_keys`, lui, s'applique dans une transaction ouverte :
        mesuré, il accepte un enfant inséré avant son parent et vérifie le tout
        au `COMMIT`. Il se remet seul à la fin de la transaction, donc aucun
        réglage ne fuit vers l'emprunteur suivant.

        Ce que cela ne fait **pas**, et qui distingue SQLite de MariaDB : ce
        n'est pas une désactivation. Un enfant dont le parent n'existe toujours
        pas au `COMMIT` fait échouer le chargement entier. C'est le cycle de
        dépendances que l'option sert à charger, pas un jeu incohérent.
        """
        return [f"PRAGMA defer_foreign_keys = {'OFF' if enabled else 'ON'}"]

    # ── DDL du socle Auth/User (ADR-084) ─────────────────────────────────────

    def auto_increment_primary_key_ddl(self, column: str, sql_type: str) -> str:
        # SQLite impose INTEGER pour la PK auto-incrémentée ; le type passé est ignoré.
        return f"{column} INTEGER PRIMARY KEY AUTOINCREMENT"

    def char_type(self, length: int) -> str:
        # SQLite ignore la longueur (affinité TEXT).
        return "TEXT"

    def boolean_default_literal(self, value: bool) -> str:
        # Pas de type booléen natif : colonne INTEGER, littéraux 1/0.
        return "1" if value else "0"

    def timestamp_default_clause(self, *, on_update: bool) -> str:
        # SQLite n'a pas d'ON UPDATE CURRENT_TIMESTAMP déclaratif : la mise à
        # jour de la colonne est à la charge de l'application (ou d'un trigger).
        return "DEFAULT CURRENT_TIMESTAMP"

    def collated_table_suffix(self) -> str:
        return ""

    # ── Pagination (DML) ─────────────────────────────────────────────────────


    # ── Horodatage serveur (DML, OPTIN-DML-DIALECT-001) ──────────────────────

    def now_expression(self) -> str:
        """`CURRENT_TIMESTAMP`, la même valeur que la clause DEFAULT."""
        return "CURRENT_TIMESTAMP"

    def interval_seconds_expression(self, base: str) -> str:
        # `datetime()` veut un modificateur textuel : on le compose, le
        # marqueur ne pouvant pas vivre dans un littéral.
        return f"datetime({base}, '+' || ? || ' seconds')"

    def pagination_clause(self) -> str:
        return " LIMIT ? OFFSET ?"

    def limit_clause(self) -> str:
        return " LIMIT ?"

    def pagination_param_order(self) -> tuple[str, str]:
        return ("limit", "offset")

    def single_row_subquery(self, column: str, table: str, where: str) -> str:
        """Sous-requête scalaire bornée à une ligne (FIXTURES-REFERENCE-DIALECT-001)."""
        return f"(SELECT {column} FROM {table} WHERE {where} LIMIT 1)"

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
        """Pose de FK many_to_one, dans les limites d'ALTER TABLE SQLite.

        SQLite ne supporte pas ALTER TABLE ... ADD CONSTRAINT. Quand la colonne
        est créée par relations.sql (`add_column`), la contrainte est portée
        inline par ADD COLUMN (clause CONSTRAINT ... REFERENCES), réellement
        applicable. Deux limites sont révélées par un commentaire SQL plutôt que
        masquées (règle B, ADR-084) : une colonne ajoutée avec REFERENCES doit
        avoir NULL pour défaut (la colonne est donc créée nullable même si la
        relation est NOT NULL, contrainte à faire respecter par l'application) ;
        et une colonne déjà déclarée par l'entité ne peut plus recevoir de
        contrainte après coup (aucun énoncé n'est émis, seulement le commentaire).
        """
        if not add_column:
            return [
                "-- SQLite ne supporte pas ALTER TABLE ... ADD CONSTRAINT : la contrainte\n"
                f"-- {constraint_name} (FOREIGN KEY ({column}) REFERENCES {ref_table} ({ref_column}))\n"
                f"-- ne peut pas être ajoutée après coup sur la colonne existante {table}.{column}.\n"
                f"-- Portez la clause REFERENCES dans le CREATE TABLE de {table}, ou recréez la\n"
                "-- table. Voir ADR-084."
            ]
        statements: list[str] = []
        if not nullable:
            statements.append(
                "-- SQLite : une colonne NOT NULL ajoutée par ALTER TABLE exige un défaut non\n"
                "-- nul, incompatible avec une clause REFERENCES (défaut NULL exigé). La colonne\n"
                f"-- {column} est créée nullable ; NOT NULL est à faire respecter par\n"
                "-- l'application. Voir ADR-084."
            )
        statements.append(
            f"ALTER TABLE {table}\n"
            f"    ADD COLUMN {column} {sql_type} NULL\n"
            f"    CONSTRAINT {constraint_name}\n"
            f"    REFERENCES {ref_table} ({ref_column})\n"
            f"    ON DELETE {on_delete}\n"
            f"    ON UPDATE {on_update};"
        )
        if index_name is not None:
            statements.append(self.create_index_sql(table, index_name, column))
        return statements

    def introspect_columns(
        self, connection: Any, table: str, database: str
    ) -> "list[tuple[str, str, bool, bool]]":
        # PRAGMA n'accepte pas de paramètre lié : on valide le nom de table.
        if not _SAFE_IDENTIFIER.fullmatch(table):
            raise ValueError(f"Nom de table SQLite invalide : {table!r}")
        cursor = connection.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table})")
            rows = cursor.fetchall()
        finally:
            cursor.close()
        # row : (cid, name, type, notnull, dflt_value, pk)
        #
        # `INTEGER PRIMARY KEY` est l'alias du rowid : SQLite le déclare
        # `notnull = 0` alors qu'il refuse toute valeur NULL. Le rapporter
        # nullable ferait voir une différence à chaque diff de clé primaire,
        # sur une colonne pourtant conforme.
        return [
            (
                str(row[1]),
                str(row[2]),
                int(row[3]) == 0 and not _is_rowid_alias(row),
                _is_rowid_alias(row),
            )
            for row in rows
        ]
