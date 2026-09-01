# pyright: strict
# pyright: reportMissingTypeStubs=false
"""
forge_mvc_mariadb.dialect — Traits SQL MariaDB (ADR-054)
========================================================
Mapping des types Forge vers les types de colonne MariaDB. Reproduit à
l'identique le mapping historiquement codé dans le normaliseur du cœur, pour
ne rien changer au SQL généré tant que le backend est MariaDB.
"""
from typing import Any

from core.database.literals import render_literal_value

# Types Forge « simples » → type de colonne MariaDB.
# boolean → BOOLEAN (et non TINYINT(1)) : voir la note du normaliseur.
_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INT",
    "big_integer": "BIGINT",
    "float":       "DOUBLE",
    "boolean":     "BOOLEAN",
    "date":        "DATE",
    "datetime":    "DATETIME",
    "email":       "VARCHAR(255)",
    "password":    "VARCHAR(255)",
    "slug":        "VARCHAR(180)",
    "json":        "LONGTEXT",
}

# Préfixes de types SQL MariaDB par famille Python (compatibilité sql/python).
_INTEGER_PREFIXES = ("INT", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT")
_FLOAT_PREFIXES = ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")
_STRING_PREFIXES = ("CHAR", "VARCHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")


def _escape_mariadb_string(value: str, *, national: bool = False) -> str:
    """Littéral de chaîne MariaDB : antislash **et** apostrophe échappés.

    MariaDB est le seul des quatre backends où l'antislash est un caractère
    d'échappement dans les littéraux, `NO_BACKSLASH_ESCAPES` étant désactivé par
    défaut. Doubler la seule apostrophe, ce que fait la norme SQL et donc
    `core.database.literals.escape_string`, y laisse deux trous mesurés :

    - une valeur terminée par un antislash échappe le guillemet fermant et
      laisse la chaîne ouverte, ce qui casse l'instruction ;
    - une valeur comme ``a\\' OR 1=1 -- `` referme la chaîne et **exécute** la
      suite. Vérifié sur serveur : la requête rendait 1.

    PostgreSQL (`standard_conforming_strings` à `on`), SQLite et SQL Server
    traitent l'antislash comme un caractère ordinaire ; eux gardent
    `escape_string`. Le correctif appartient donc au dialecte MariaDB, pas au
    cœur, qui implémente correctement la norme.

    L'antislash est traité **avant** l'apostrophe : l'ordre inverse
    échapperait les antislashes que l'on vient d'introduire.
    """
    protege = value.replace("\\", "\\\\").replace("'", "''")
    prefix = "N" if national else ""
    return f"{prefix}'{protege}'"


class MariaDBDialect:
    """Traits SQL de MariaDB."""

    def string_type(self, max_length: int) -> str:
        return f"VARCHAR({max_length})"

    def decimal_type(self, precision: int, scale: int) -> str:
        return f"DECIMAL({precision},{scale})"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        return "BIGINT UNSIGNED"

    def identity_storage_type(self) -> str:
        # MariaDB : AUTO_INCREMENT est une clause à part, le type de colonne
        # est déjà un type de stockage ordinaire. Les deux coïncident.
        return "BIGINT UNSIGNED"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        n = sql_type.strip().upper()
        # `BOOLEAN` est un ALIAS de `TINYINT(1)` : MariaDB accepte le premier et
        # stocke le second, que l'introspection rapporte. Les deux désignent donc
        # le même type physique et doivent rendre les mêmes familles, sans quoi
        # un diff de schéma signale une différence sur chaque colonne booléenne.
        #
        # Le test doit précéder celui des entiers, `TINYINT(1)` commençant par
        # `TINYINT`. Un `TINYINT` sans largeur reste un petit entier.
        #
        # Deux familles plutôt qu'une, sur le modèle de `forge-mvc-sqlite` dont
        # l'`INTEGER` rend déjà `("int", "bool")` : le type est réellement les
        # deux, et la validation `python_type` accepte l'un comme l'autre.
        if n in {"BOOL", "BOOLEAN"} or n.startswith("TINYINT(1)"):
            return ("int", "bool")
        if n == "DATE":
            return ("date",)
        if n in {"DATETIME", "TIMESTAMP"}:
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
        return ()

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        return f"{column} {sql_type} NOT NULL AUTO_INCREMENT"

    def auto_increment_clause(self) -> str:
        # MariaDB separe le type et l'auto-increment.
        return "AUTO_INCREMENT"

    def emits_separate_primary_key(self) -> bool:
        return True

    def unique_is_column_constraint(self) -> bool:
        return False

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        return f"UNIQUE KEY uk_{table}_{field_name} ({column})"

    def table_suffix(self) -> str:
        return " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4"

    def create_table_opening(self, table: str) -> str:
        return f"CREATE TABLE IF NOT EXISTS {table}"

    def forge_migrations_ddl(self) -> str:
        return (
            "CREATE TABLE IF NOT EXISTS forge_migrations (\n"
            "    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,\n"
            "    version VARCHAR(64) NOT NULL,\n"
            "    name VARCHAR(255) NOT NULL,\n"
            "    filename VARCHAR(255) NOT NULL,\n"
            "    checksum CHAR(64) NOT NULL,\n"
            "    applied_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,\n"
            "    execution_ms INT NULL,\n"
            "    UNIQUE KEY uq_forge_migrations_version (version),\n"
            "    UNIQUE KEY uq_forge_migrations_filename (filename)\n"
            ") ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
        )

    def supports_transactional_ddl(self) -> bool:
        """Faux : MariaDB valide implicitement autour de chaque instruction DDL.

        Seul des quatre backends dans ce cas. Mesuré : une migration à deux
        `CREATE TABLE` dont le second est fautif laisse la première table en
        place malgré le `ROLLBACK`, là où PostgreSQL et SQL Server annulent
        les deux.
        """
        return False

    def quote_identifier(self, name: str) -> str:
        # Le backtick contenu dans le nom se double, sans quoi il referme la
        # citation et la suite du nom devient de la syntaxe.
        return "`" + name.replace("`", "``") + "`"

    def render_literal(self, value: object) -> str:
        # Booléens 1/0, dates en chaîne ISO quotée (ADR-075).
        return render_literal_value(
            value,
            bool_true="1",
            bool_false="0",
            render_string=_escape_mariadb_string,
            render_date=lambda d: _escape_mariadb_string(d.isoformat()),
            render_datetime=lambda dt: _escape_mariadb_string(dt.strftime("%Y-%m-%d %H:%M:%S")),
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        defs = [
            f"    ADD COLUMN {self.quote_identifier(name)} {definition}"
            for name, definition in columns
        ]
        return f"ALTER TABLE {self.quote_identifier(table)}\n" + ",\n".join(defs) + ";\n"

    def named_unique(self, name: str, columns: "list[str]") -> str:
        return f"UNIQUE KEY {name} ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return True

    def index_clause(self, name: str, column: str) -> str:
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        return f"CREATE INDEX {name} ON {table} ({column});"

    def server_diagnostics_sql(self) -> "dict[str, str]":
        return {
            "version": "SELECT VERSION() AS value",
            "encodage": "SELECT @@character_set_database AS value",
            "collation": "SELECT @@collation_database AS value",
            "base": "SELECT DATABASE() AS value",
            "compte": "SELECT CURRENT_USER() AS value",
        }

    def add_column_clause(self, table: str, definition: str) -> str:
        return f"ALTER TABLE {table} ADD COLUMN {definition};"

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        # Levier de session MariaDB (ADR-077).
        return [f"SET FOREIGN_KEY_CHECKS = {1 if enabled else 0}"]

    # ── DDL du socle Auth/User (ADR-084) ─────────────────────────────────────

    def auto_increment_primary_key_ddl(self, column: str, sql_type: str) -> str:
        return f"{column} {sql_type} AUTO_INCREMENT PRIMARY KEY"

    def char_type(self, length: int) -> str:
        return f"CHAR({length})"

    def boolean_default_literal(self, value: bool) -> str:
        return "TRUE" if value else "FALSE"

    def timestamp_default_clause(self, *, on_update: bool) -> str:
        """Défaut d'horodatage, **en UTC**, comme toutes les colonnes de Forge.

        `CURRENT_TIMESTAMP` rendait l'heure **locale du serveur** ici, alors
        que SQLite et SQL Server rendaient déjà de l'UTC : une même base
        portait deux référentiels selon le backend, et la rétention d'audit
        comparait une borne calculée en UTC par Python à des valeurs locales
        (`DIALECT-UTC-DEFAULT-001`).

        `on_update` n'est plus honoré, et c'est mesuré : MariaDB **refuse**
        `ON UPDATE UTC_TIMESTAMP()`, n'acceptant que `CURRENT_TIMESTAMP` dans
        cette clause. La tenir aurait mis deux référentiels dans une seule
        colonne, le défaut en UTC et la mise à jour en heure locale, ce qui est
        pire que le défaut d'origine. La colonne est donc écrite par Python,
        seule autorité selon l'ADR-081.
        """
        return "DEFAULT UTC_TIMESTAMP"

    def collated_table_suffix(self) -> str:
        return " ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"

    # ── Pagination (DML) ─────────────────────────────────────────────────────


    # ── Horodatage serveur (DML, OPTIN-DML-DIALECT-001) ──────────────────────

    def now_expression(self) -> str:
        """L'instant présent **en UTC**, la même horloge que la clause DEFAULT.

        Cette docstring disait déjà « la même valeur que la clause DEFAULT », et
        c'est une propriété que le dépôt vérifie. Passer le défaut en UTC sans
        passer celle-ci aurait donc désynchronisé les deux horloges d'un même
        moteur : `forge-mvc-jobs` compare `available_at <= <expression>`, et un
        travail daté en UTC comparé à l'heure locale serait pris deux heures
        trop tôt. Pire que le défaut d'origine (`DIALECT-UTC-DEFAULT-001`).
        """
        return "UTC_TIMESTAMP"

    def interval_seconds_expression(self, base: str) -> str:
        return f"{base} + INTERVAL ? SECOND"

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
            cursor.execute(
                "SELECT COLUMN_NAME, COLUMN_TYPE, IS_NULLABLE, EXTRA "
                "FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = ? AND TABLE_NAME = ? "
                "ORDER BY ORDINAL_POSITION",
                (database, table),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [
            (
                str(row[0]),
                str(row[1]),
                str(row[2]).upper() == "YES",
                "auto_increment" in str(row[3]).lower(),
            )
            for row in rows
        ]
