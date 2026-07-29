# pyright: strict
"""
forge_mvc_postgres.dialect — Traits SQL PostgreSQL (ADR-054)
============================================================
Mapping des types Forge vers PostgreSQL et primitives DDL. La clé primaire
auto-incrémentée utilise BIGSERIAL ; les index sont des instructions CREATE
INDEX séparées (PostgreSQL n'accepte pas d'index dans le CREATE TABLE).
"""
from typing import Any

from core.database.literals import escape_string, render_literal_value

_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INTEGER",
    "big_integer": "BIGINT",
    "float":       "DOUBLE PRECISION",
    "boolean":     "BOOLEAN",
    "date":        "DATE",
    "datetime":    "TIMESTAMP",
    "email":       "VARCHAR(255)",
    "password":    "VARCHAR(255)",
    "slug":        "VARCHAR(180)",
    "json":        "JSONB",
}

# Préfixes de types PostgreSQL par famille Python (validation sql/python).
_INTEGER_PREFIXES = ("INT", "BIGINT", "SMALLINT", "BIGSERIAL", "SERIAL", "SMALLSERIAL")
_FLOAT_PREFIXES = ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")
_STRING_PREFIXES = ("CHAR", "VARCHAR", "TEXT", "JSON", "JSONB", "UUID")


def _sized_type(data_type: str, length: Any, precision: Any, scale: Any) -> str:
    """Recompose un type introspecté avec sa longueur ou sa précision.

    `information_schema.data_type` ne porte que le nom (« character varying »,
    « numeric ») : sans cette recomposition, un diff de schéma ne peut pas
    comparer `VARCHAR(255)` à ce qui est réellement en base.

    La précision n'est ajoutée qu'aux types décimaux : PostgreSQL renseigne
    `numeric_precision` pour tous les numériques, y compris `integer`, où
    elle ne fait pas partie de la déclaration.
    """
    if length is not None:
        return f"{data_type}({int(length)})"
    if data_type.lower() in {"numeric", "decimal"} and precision is not None:
        return f"{data_type}({int(precision)},{int(scale or 0)})"
    return data_type


class PostgreSQLDialect:
    """Traits SQL de PostgreSQL."""

    def string_type(self, max_length: int) -> str:
        return f"VARCHAR({max_length})"

    def decimal_type(self, precision: int, scale: int) -> str:
        return f"NUMERIC({precision},{scale})"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        return "BIGSERIAL"

    def identity_storage_type(self) -> str:
        # BIGSERIAL n'est pas un type : c'est un BIGINT plus une séquence et un
        # DEFAULT nextval(). Une colonne de clé étrangère doit être un BIGINT nu,
        # sans quoi elle se verrait attribuer une valeur toute seule.
        return "BIGINT"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        n = sql_type.strip().upper()
        if n == "DATE":
            return ("date",)
        if n.startswith("TIMESTAMP"):
            return ("datetime",)
        for prefix in _INTEGER_PREFIXES:
            if n.startswith(prefix):
                return ("int",)
        for prefix in _FLOAT_PREFIXES:
            if n.startswith(prefix):
                return ("float",)
        for prefix in _STRING_PREFIXES:
            if n.startswith(prefix):
                return ("str",)
        if n in {"BOOL", "BOOLEAN"}:
            return ("bool",)
        return ()

    # ── DDL ──────────────────────────────────────────────────────────────────

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        # BIGSERIAL crée la séquence et implique NOT NULL ; le type passé est
        # ignoré (la PK auto-incrémentée est toujours un serial).
        return f"{column} BIGSERIAL"

    def auto_increment_clause(self) -> str:
        # L'auto-increment est PORTE PAR LE TYPE (BIGSERIAL) : aucun mot-cle.
        return ""

    def emits_separate_primary_key(self) -> bool:
        return True

    def unique_is_column_constraint(self) -> bool:
        # Unicité portée par la colonne, pour éviter les soucis d'ordre des
        # contraintes de table.
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
            "    id BIGSERIAL PRIMARY KEY,\n"
            "    version VARCHAR(64) NOT NULL,\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    filename VARCHAR(255) NOT NULL,\n"
            "    checksum CHAR(64) NOT NULL,\n"
            "    applied_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "    execution_ms INTEGER,\n"
            "    UNIQUE (version),\n"
            "    UNIQUE (filename)\n"
            ")"
        )

    def supports_transactional_ddl(self) -> bool:
        """Vrai : PostgreSQL annule la DDL comme le DML. Vérifié sur serveur réel."""
        return True

    def quote_identifier(self, name: str) -> str:
        # Le guillemet contenu dans le nom se double, sans quoi il referme la
        # citation et la suite du nom devient de la syntaxe.
        return '"' + name.replace('"', '""') + '"'

    def render_literal(self, value: object) -> str:
        # PostgreSQL : booléens TRUE/FALSE, dates typées DATE '...' / TIMESTAMP '...' (ADR-075).
        return render_literal_value(
            value,
            bool_true="TRUE",
            bool_false="FALSE",
            render_string=escape_string,
            render_date=lambda d: f"DATE {escape_string(d.isoformat())}",
            render_datetime=lambda dt: f"TIMESTAMP {escape_string(dt.strftime('%Y-%m-%d %H:%M:%S'))}",
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        defs = [
            f"    ADD COLUMN {self.quote_identifier(name)} {definition}"
            for name, definition in columns
        ]
        return f"ALTER TABLE {self.quote_identifier(table)}\n" + ",\n".join(defs) + ";\n"

    def named_unique(self, name: str, columns: "list[str]") -> str:
        return f"CONSTRAINT {name} UNIQUE ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return False

    def index_clause(self, name: str, column: str) -> str:
        # Non utilisé (index hors CREATE TABLE) ; fourni pour le contrat.
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        return f"CREATE INDEX IF NOT EXISTS {name} ON {table} ({column});"

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        # PostgreSQL n'a pas d'interrupteur FK ; session_replication_role =
        # replica court-circuite les triggers (dont les contraintes FK). Exige un
        # rôle superuser (ADR-077).
        return [f"SET session_replication_role = {'origin' if enabled else 'replica'}"]

    # ── DDL du socle Auth/User (ADR-084) ─────────────────────────────────────

    def auto_increment_primary_key_ddl(self, column: str, sql_type: str) -> str:
        # SERIAL crée la séquence et implique NOT NULL ; BIGSERIAL si le type
        # demandé est un entier large.
        serial = "BIGSERIAL" if "BIG" in sql_type.upper() else "SERIAL"
        return f"{column} {serial} PRIMARY KEY"

    def char_type(self, length: int) -> str:
        return f"CHAR({length})"

    def boolean_default_literal(self, value: bool) -> str:
        return "TRUE" if value else "FALSE"

    def timestamp_default_clause(self, *, on_update: bool) -> str:
        # PostgreSQL n'a pas d'ON UPDATE CURRENT_TIMESTAMP déclaratif : la mise
        # à jour de la colonne est à la charge de l'application (ou d'un trigger).
        return "DEFAULT CURRENT_TIMESTAMP"

    def collated_table_suffix(self) -> str:
        return ""

    # ── Pagination (DML) ─────────────────────────────────────────────────────

    def pagination_clause(self) -> str:
        return " LIMIT ? OFFSET ?"

    def limit_clause(self) -> str:
        return " LIMIT ?"

    def pagination_param_order(self) -> tuple[str, str]:
        return ("limit", "offset")

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
        statements: list[str] = []
        if add_column:
            null_sql = "NULL" if nullable else "NOT NULL"
            statements.append(
                f"ALTER TABLE {table}\n"
                f"    ADD COLUMN {column} {sql_type} {null_sql};"
            )
        statements.append(
            f"ALTER TABLE {table}\n"
            f"    ADD CONSTRAINT {constraint_name}\n"
            f"    FOREIGN KEY ({column})\n"
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
        cursor = connection.cursor()
        try:
            # Paramètres « ? » : l'adaptateur de connexion les traduit en « %s ».
            # Le filtre de schéma est indispensable : `information_schema`
            # expose toutes les tables visibles de la base, donc une homonyme
            # dans un autre schéma ferait remonter ses colonnes en plus des
            # bonnes, entrelacées par `ordinal_position`.
            cursor.execute(
                "SELECT column_name, data_type, is_nullable, column_default, "
                "character_maximum_length, numeric_precision, numeric_scale "
                "FROM information_schema.columns "
                "WHERE table_name = ? AND table_schema = current_schema() "
                "ORDER BY ordinal_position",
                (table,),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [
            (
                str(row[0]),
                _sized_type(str(row[1]), row[4], row[5], row[6]),
                str(row[2]).upper() == "YES",
                str(row[3] or "").lower().startswith("nextval"),
            )
            for row in rows
        ]
