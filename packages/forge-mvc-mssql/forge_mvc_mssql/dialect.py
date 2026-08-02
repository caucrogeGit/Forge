# pyright: strict
"""
forge_mvc_mssql.dialect — Traits SQL Microsoft SQL Server (ADR-054)
==================================================================
Mapping des types Forge vers SQL Server (Transact-SQL) et primitives DDL.
Particularités : clé primaire auto-incrémentée via ``IDENTITY(1,1)``,
identifiants entre crochets ``[...]``, absence de ``IF NOT EXISTS`` (formes
gardées ``IF OBJECT_ID(...) IS NULL`` / ``IF NOT EXISTS (SELECT ...)``), et
index en instructions séparées.
"""
from typing import Any

from core.database.literals import escape_string, render_literal_value

_SIMPLE_TYPES: dict[str, str] = {
    "text":        "NVARCHAR(MAX)",
    "integer":     "INT",
    "big_integer": "BIGINT",
    "float":       "FLOAT",
    "boolean":     "BIT",
    "date":        "DATE",
    "datetime":    "DATETIME2",
    "email":       "NVARCHAR(255)",
    "password":    "NVARCHAR(255)",
    "slug":        "NVARCHAR(180)",
    "json":        "NVARCHAR(MAX)",
}

_INTEGER_PREFIXES = ("INT", "BIGINT", "SMALLINT", "TINYINT")
_FLOAT_PREFIXES = ("FLOAT", "REAL", "DECIMAL", "NUMERIC", "MONEY")
_STRING_PREFIXES = ("CHAR", "VARCHAR", "NCHAR", "NVARCHAR", "TEXT", "NTEXT", "UNIQUEIDENTIFIER")
_DATETIME_PREFIXES = ("DATETIME", "SMALLDATETIME")


def _sized_type(data_type: str, length: Any, precision: Any, scale: Any) -> str:
    """Recompose un type introspecté avec sa longueur ou sa précision.

    `INFORMATION_SCHEMA.DATA_TYPE` ne porte que le nom (« NVARCHAR »,
    « DECIMAL ») : sans cette recomposition, un diff de schéma ne peut pas
    comparer `NVARCHAR(255)` à ce qui est réellement en base.

    Une longueur de -1 signale `MAX` en T-SQL. La précision n'est ajoutée
    qu'aux types décimaux : SQL Server renseigne `NUMERIC_PRECISION` pour tous
    les numériques, y compris `INT`, où elle ne fait pas partie de la
    déclaration.
    """
    if length is not None:
        return f"{data_type}(MAX)" if int(length) == -1 else f"{data_type}({int(length)})"
    if data_type.upper() in {"DECIMAL", "NUMERIC"} and precision is not None:
        return f"{data_type}({int(precision)},{int(scale or 0)})"
    return data_type


class MSSQLDialect:
    """Traits SQL de Microsoft SQL Server."""

    def string_type(self, max_length: int) -> str:
        return f"NVARCHAR({max_length})"

    def decimal_type(self, precision: int, scale: int) -> str:
        return f"DECIMAL({precision},{scale})"

    def simple_type(self, forge_type: str) -> str:
        return _SIMPLE_TYPES[forge_type]

    def identity_type(self) -> str:
        return "BIGINT IDENTITY(1,1)"

    def identity_storage_type(self) -> str:
        # IDENTITY est une propriété de colonne, pas un type. SQL Server
        # n'admet qu'une seule colonne IDENTITY par table, déjà prise par la
        # clé primaire : une clé étrangère doit être un BIGINT nu.
        return "BIGINT"

    def sql_families(self, sql_type: str) -> tuple[str, ...]:
        n = sql_type.strip().upper()
        if n == "DATE":
            return ("date",)
        for prefix in _DATETIME_PREFIXES:
            if n.startswith(prefix):
                return ("datetime",)
        if n in {"BIT", "BOOL", "BOOLEAN"}:
            return ("bool",)
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

    # ── DDL ──────────────────────────────────────────────────────────────────

    def auto_increment_column_ddl(self, column: str, sql_type: str) -> str:
        # IDENTITY(1,1) gère l'auto-incrément ; le type passé est ignoré.
        return f"{column} BIGINT IDENTITY(1,1)"

    def auto_increment_clause(self) -> str:
        # L'auto-increment est PORTE PAR LE TYPE (IDENTITY(1,1)) : aucun mot-cle.
        return ""

    def emits_separate_primary_key(self) -> bool:
        return True

    def unique_is_column_constraint(self) -> bool:
        return True

    def unique_constraint_ddl(self, table: str, field_name: str, column: str) -> str:
        return f"UNIQUE ({column})"

    def table_suffix(self) -> str:
        return ""

    def create_table_opening(self, table: str) -> str:
        # SQL Server n'a pas CREATE TABLE IF NOT EXISTS.
        return f"IF OBJECT_ID(N'{table}', N'U') IS NULL\nCREATE TABLE {table}"

    def forge_migrations_ddl(self) -> str:
        return (
            "IF OBJECT_ID(N'forge_migrations', N'U') IS NULL\n"
            "CREATE TABLE forge_migrations (\n"
            "    id BIGINT IDENTITY(1,1) PRIMARY KEY,\n"
            "    version NVARCHAR(64) NOT NULL,\n"
            "    name NVARCHAR(255) NOT NULL,\n"
            "    filename NVARCHAR(255) NOT NULL,\n"
            "    checksum CHAR(64) NOT NULL,\n"
            "    applied_at DATETIME2 NOT NULL DEFAULT SYSUTCDATETIME(),\n"
            "    execution_ms INT,\n"
            "    CONSTRAINT uq_forge_migrations_version UNIQUE (version),\n"
            "    CONSTRAINT uq_forge_migrations_filename UNIQUE (filename)\n"
            ")"
        )

    def supports_transactional_ddl(self) -> bool:
        """Vrai : SQL Server annule la DDL comme le DML. Vérifié sur serveur réel."""
        return True

    def quote_identifier(self, name: str) -> str:
        # Seul le crochet fermant referme la citation : c'est lui qui se
        # double, le crochet ouvrant étant ordinaire à l'intérieur.
        return "[" + name.replace("]", "]]") + "]"

    def render_literal(self, value: object) -> str:
        # SQL Server : chaînes Unicode N'...', booléens (BIT) 1/0, dates ISO (ADR-075).
        return render_literal_value(
            value,
            bool_true="1",
            bool_false="0",
            render_string=lambda s: escape_string(s, national=True),
            render_date=lambda d: escape_string(d.isoformat()),
            render_datetime=lambda dt: escape_string(dt.strftime("%Y-%m-%d %H:%M:%S")),
        )

    def add_columns_sql(self, table: str, columns: "list[tuple[str, str]]") -> str:
        # SQL Server : un seul ALTER TABLE ... ADD col def, col def (sans COLUMN).
        defs = [
            f"{self.quote_identifier(name)} {definition}"
            for name, definition in columns
        ]
        return (
            f"ALTER TABLE {self.quote_identifier(table)}\n"
            "    ADD " + ",\n        ".join(defs) + ";\n"
        )

    def named_unique(self, name: str, columns: "list[str]") -> str:
        return f"CONSTRAINT {name} UNIQUE ({', '.join(columns)})"

    def inline_indexes(self) -> bool:
        return False

    def index_clause(self, name: str, column: str) -> str:
        return f"INDEX {name} ({column})"

    def create_index_sql(self, table: str, name: str, column: str) -> str:
        # SQL Server n'a pas CREATE INDEX IF NOT EXISTS : forme gardée.
        return (
            f"IF NOT EXISTS (SELECT 1 FROM sys.indexes "
            f"WHERE name = '{name}' AND object_id = OBJECT_ID('{table}'))\n"
            f"    CREATE INDEX {name} ON {table} ({column});"
        )

    def foreign_key_checks_ddl(self, *, enabled: bool) -> "list[str]":
        # SQL Server ne désactive les contraintes que table par table
        # (ALTER TABLE ... NOCHECK CONSTRAINT), sans levier de session : pas de
        # forme générale ici. Le chargement s'appuie sur l'ordre topologique.
        return []

    # ── DDL du socle Auth/User (ADR-084) ─────────────────────────────────────

    def auto_increment_primary_key_ddl(self, column: str, sql_type: str) -> str:
        return f"{column} {sql_type} IDENTITY(1,1) PRIMARY KEY"

    def char_type(self, length: int) -> str:
        return f"CHAR({length})"

    def boolean_default_literal(self, value: bool) -> str:
        # BIT : littéraux 1/0.
        return "1" if value else "0"

    def timestamp_default_clause(self, *, on_update: bool) -> str:
        # Pas d'ON UPDATE déclaratif en T-SQL (trigger sinon) ; SYSUTCDATETIME()
        # par cohérence avec forge_migrations_ddl.
        return "DEFAULT SYSUTCDATETIME()"

    def collated_table_suffix(self) -> str:
        return ""

    # ── Pagination (DML) ─────────────────────────────────────────────────────


    # ── Horodatage serveur (DML, OPTIN-DML-DIALECT-001) ──────────────────────

    def now_expression(self) -> str:
        """`SYSUTCDATETIME()`, la même valeur que la clause DEFAULT.

        `CURRENT_TIMESTAMP` existe aussi en T-SQL mais rend l'heure locale du
        serveur, alors que les colonnes de Forge y sont posées en UTC : les
        deux lignes ne seraient pas comparables.
        """
        return "SYSUTCDATETIME()"

    def interval_seconds_expression(self, base: str) -> str:
        return f"DATEADD(second, ?, {base})"

    def pagination_clause(self) -> str:
        # T-SQL n'a pas de LIMIT. Cette forme exige un ORDER BY dans la requête.
        return " OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"

    def limit_clause(self) -> str:
        # Pas de LIMIT en T-SQL ; le décalage nul est explicite. Exige un ORDER BY.
        return " OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY"

    def pagination_param_order(self) -> tuple[str, str]:
        # Le décalage est annoncé avant le nombre de lignes, contrairement à LIMIT.
        return ("offset", "limit")

    def single_row_subquery(self, column: str, table: str, where: str) -> str:
        """Sous-requête scalaire bornée à une ligne (FIXTURES-REFERENCE-DIALECT-001).

        T-SQL n'a pas de `LIMIT` : la borne s'écrit `TOP 1` en tête du `SELECT`,
        et non en suffixe. C'est cette asymétrie qui rendait `limit_clause()`
        inutilisable ici.
        """
        return f"(SELECT TOP 1 {column} FROM {table} WHERE {where})"

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
        # T-SQL ne connaît pas RESTRICT : NO ACTION en est l'équivalent.
        on_delete = "NO ACTION" if on_delete == "RESTRICT" else on_delete
        on_update = "NO ACTION" if on_update == "RESTRICT" else on_update
        statements: list[str] = []
        if add_column:
            # T-SQL : ALTER TABLE ... ADD (sans mot-clé COLUMN).
            null_sql = "NULL" if nullable else "NOT NULL"
            statements.append(
                f"ALTER TABLE {table}\n"
                f"    ADD {column} {sql_type} {null_sql};"
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
            # pyodbc utilise nativement les paramètres « ? ».
            # Le filtre de schéma est indispensable : `INFORMATION_SCHEMA`
            # expose toutes les tables visibles de la base, donc une homonyme
            # dans un autre schéma ferait remonter ses colonnes en plus des
            # bonnes, entrelacées par `ORDINAL_POSITION`. `SCHEMA_NAME()` rend
            # le schéma par défaut de l'utilisateur, celui que résout aussi
            # `OBJECT_ID` sur un nom non qualifié.
            cursor.execute(
                "SELECT c.COLUMN_NAME, c.DATA_TYPE, c.IS_NULLABLE, "
                "COLUMNPROPERTY(OBJECT_ID(?), c.COLUMN_NAME, 'IsIdentity'), "
                "c.CHARACTER_MAXIMUM_LENGTH, c.NUMERIC_PRECISION, c.NUMERIC_SCALE "
                "FROM INFORMATION_SCHEMA.COLUMNS c "
                "WHERE c.TABLE_NAME = ? AND c.TABLE_SCHEMA = SCHEMA_NAME() "
                "ORDER BY c.ORDINAL_POSITION",
                (table, table),
            )
            rows = cursor.fetchall()
        finally:
            cursor.close()
        return [
            (
                str(row[0]),
                _sized_type(str(row[1]).upper(), row[4], row[5], row[6]),
                str(row[2]).upper() == "YES",
                bool(row[3]),
            )
            for row in rows
        ]
