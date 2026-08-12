# pyright: strict
"""Rendu dialectal du DDL du socle Auth/User (AUTH-INIT-DIALECT-DDL-001, ADR-084).

Les sept tables du socle Auth/User sont décrites ici par des specs déclaratives,
et `render_auth_sql(table_name, dialect)` les rend dans le dialecte du backend
BDD actif. Les constantes MariaDB historiques de `cli.security.auth`
(USERS_SQL, AUTH_TOKENS_SQL, ...) restent la référence canonique : le rendu de
ces specs avec le dialecte MariaDB leur est strictement égal (test de parité),
ce qui verrouille la source unique.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.database.backend import Dialect


@dataclass(frozen=True)
class AuthColumn:
    """Colonne d'une table Auth/User, en traits dialectaux.

    `forge_type` : identity (PK auto-incrémentée inline), integer, text,
    datetime, boolean, string (avec `length`), char (avec `length`).
    """

    name: str
    forge_type: str
    length: int = 0
    nullable: bool = False
    unique: bool = False
    default_bool: bool | None = None
    default_sql: str = ""
    timestamp_default: bool = False
    timestamp_on_update: bool = False


@dataclass(frozen=True)
class AuthIndex:
    name: str
    columns: tuple[str, ...]


@dataclass(frozen=True)
class AuthForeignKey:
    constraint_name: str
    column: str
    ref_table: str
    ref_column: str
    on_delete: str


@dataclass(frozen=True)
class AuthTableSpec:
    table: str
    columns: tuple[AuthColumn, ...]
    primary_key: tuple[str, ...] = ()
    indexes: tuple[AuthIndex, ...] = ()
    foreign_keys: tuple[AuthForeignKey, ...] = ()


def _identity() -> AuthColumn:
    return AuthColumn("id", "identity")


def _created_at() -> AuthColumn:
    return AuthColumn("created_at", "datetime", timestamp_default=True)


def _updated_at() -> AuthColumn:
    return AuthColumn("updated_at", "datetime", timestamp_default=True, timestamp_on_update=True)


def _fk_users(constraint_name: str, column: str, on_delete: str) -> AuthForeignKey:
    return AuthForeignKey(constraint_name, column, "users", "id", on_delete)


AUTH_TABLE_SPECS: dict[str, AuthTableSpec] = {
    "users": AuthTableSpec(
        table="users",
        columns=(
            _identity(),
            # ADR-089 : `login` porte l'IDENTITÉ, unique et obligatoire, sans
            # contrainte de forme. `email` porte le CONTACT, facultatif et NON
            # unique, deux comptes pouvant partager une adresse de dépannage.
            AuthColumn("login", "string", length=255, unique=True),
            AuthColumn("email", "string", length=255, nullable=True),
            AuthColumn("password_hash", "string", length=255),
            AuthColumn("is_active", "boolean", default_bool=True),
            AuthColumn("email_verified_at", "datetime", nullable=True),
            _created_at(),
            _updated_at(),
        ),
    ),
    "auth_tokens": AuthTableSpec(
        table="auth_tokens",
        columns=(
            _identity(),
            AuthColumn("user_id", "integer"),
            AuthColumn("purpose", "string", length=80),
            AuthColumn("token_hash", "char", length=64, unique=True),
            AuthColumn("expires_at", "datetime"),
            AuthColumn("used_at", "datetime", nullable=True),
            _created_at(),
        ),
        indexes=(
            AuthIndex("idx_auth_tokens_user_purpose", ("user_id", "purpose")),
            AuthIndex("idx_auth_tokens_expires_at", ("expires_at",)),
        ),
        foreign_keys=(
            _fk_users("fk_auth_tokens_user_id", "user_id", "CASCADE"),
        ),
    ),
    "auth_mfa_factors": AuthTableSpec(
        table="auth_mfa_factors",
        columns=(
            _identity(),
            AuthColumn("user_id", "integer"),
            AuthColumn("factor_type", "string", length=40),
            AuthColumn("totp_secret", "string", length=255),
            AuthColumn("status", "string", length=40, default_sql="'pending'"),
            AuthColumn("label", "string", length=120, nullable=True),
            AuthColumn("confirmed_at", "datetime", nullable=True),
            AuthColumn("last_used_at", "datetime", nullable=True),
            _created_at(),
            _updated_at(),
        ),
        indexes=(
            AuthIndex("idx_auth_mfa_factors_user_id", ("user_id",)),
            AuthIndex("idx_auth_mfa_factors_user_status", ("user_id", "status")),
        ),
        foreign_keys=(
            _fk_users("fk_auth_mfa_factors_user_id", "user_id", "CASCADE"),
        ),
    ),
    "auth_mfa_recovery_codes": AuthTableSpec(
        table="auth_mfa_recovery_codes",
        columns=(
            _identity(),
            AuthColumn("user_id", "integer"),
            AuthColumn("code_hash", "char", length=64, unique=True),
            AuthColumn("used_at", "datetime", nullable=True),
            _created_at(),
            _updated_at(),
        ),
        indexes=(
            AuthIndex("idx_auth_mfa_recovery_codes_user_id", ("user_id",)),
            AuthIndex("idx_auth_mfa_recovery_codes_used_at", ("used_at",)),
        ),
        foreign_keys=(
            _fk_users("fk_auth_mfa_recovery_codes_user_id", "user_id", "CASCADE"),
        ),
    ),
    "user_roles": AuthTableSpec(
        table="user_roles",
        columns=(
            AuthColumn("user_id", "integer"),
            AuthColumn("role_id", "integer"),
            _created_at(),
        ),
        primary_key=("user_id", "role_id"),
        indexes=(
            AuthIndex("idx_user_roles_user_id", ("user_id",)),
            AuthIndex("idx_user_roles_role_id", ("role_id",)),
        ),
        foreign_keys=(
            _fk_users("fk_user_roles_user_id", "user_id", "CASCADE"),
            AuthForeignKey("fk_user_roles_role_id", "role_id", "roles", "id", "CASCADE"),
        ),
    ),
    "auth_audit_log": AuthTableSpec(
        table="auth_audit_log",
        columns=(
            _identity(),
            AuthColumn("event_type", "string", length=120),
            AuthColumn("user_id", "integer", nullable=True),
            AuthColumn("actor_user_id", "integer", nullable=True),
            AuthColumn("ip_address", "string", length=45, nullable=True),
            AuthColumn("user_agent", "string", length=255, nullable=True),
            AuthColumn("metadata_json", "text", nullable=True),
            _created_at(),
        ),
        indexes=(
            AuthIndex("idx_auth_audit_log_event_type", ("event_type",)),
            AuthIndex("idx_auth_audit_log_user_id", ("user_id",)),
            AuthIndex("idx_auth_audit_log_actor_user_id", ("actor_user_id",)),
            AuthIndex("idx_auth_audit_log_created_at", ("created_at",)),
        ),
        foreign_keys=(
            _fk_users("fk_auth_audit_log_user_id", "user_id", "SET NULL"),
            _fk_users("fk_auth_audit_log_actor_user_id", "actor_user_id", "SET NULL"),
        ),
    ),
    "auth_rate_limit_attempts": AuthTableSpec(
        table="auth_rate_limit_attempts",
        columns=(
            _identity(),
            AuthColumn("action", "string", length=120),
            AuthColumn("rate_key", "string", length=255),
            AuthColumn("ip_address", "string", length=45, nullable=True),
            AuthColumn("user_id", "integer", nullable=True),
            AuthColumn("success", "boolean", default_bool=False),
            _created_at(),
        ),
        indexes=(
            AuthIndex("idx_auth_rate_limit_action_key", ("action", "rate_key")),
            AuthIndex("idx_auth_rate_limit_created_at", ("created_at",)),
            AuthIndex("idx_auth_rate_limit_user_id", ("user_id",)),
        ),
        foreign_keys=(
            _fk_users("fk_auth_rate_limit_user_id", "user_id", "SET NULL"),
        ),
    ),
}


def _column_type(column: AuthColumn, dialect: Dialect) -> str:
    if column.forge_type == "string":
        return dialect.string_type(column.length)
    if column.forge_type == "char":
        return dialect.char_type(column.length)
    return dialect.simple_type(column.forge_type)


def _column_line(column: AuthColumn, dialect: Dialect) -> str:
    parts = [column.name, _column_type(column, dialect)]
    parts.append("NULL" if column.nullable else "NOT NULL")
    if column.unique:
        parts.append("UNIQUE")
    if column.default_bool is not None:
        parts.append(f"DEFAULT {dialect.boolean_default_literal(column.default_bool)}")
    if column.default_sql:
        parts.append(f"DEFAULT {column.default_sql}")
    if column.timestamp_default:
        parts.append(dialect.timestamp_default_clause(on_update=column.timestamp_on_update))
    return " ".join(parts)


def render_auth_sql(table_name: str, dialect: Dialect) -> str:
    """Rend le DDL complet d'une table Auth/User dans le dialecte donné.

    Le rendu comprend le CREATE TABLE idempotent et, pour les dialectes sans
    index inline (SQLite, PostgreSQL, SQL Server), les instructions
    CREATE INDEX séparées. `table_name` est une clé de `AUTH_TABLE_SPECS` ;
    une clé inconnue lève KeyError.
    """
    spec = AUTH_TABLE_SPECS[table_name]
    lines: list[str] = []
    for column in spec.columns:
        if column.forge_type == "identity":
            lines.append(
                dialect.auto_increment_primary_key_ddl(column.name, dialect.simple_type("integer"))
            )
        else:
            lines.append(_column_line(column, dialect))
    if spec.primary_key:
        lines.append(f"PRIMARY KEY ({', '.join(spec.primary_key)})")
    if dialect.inline_indexes():
        for index in spec.indexes:
            lines.append(dialect.index_clause(index.name, ", ".join(index.columns)))
    for fk in spec.foreign_keys:
        lines.append(
            f"CONSTRAINT {fk.constraint_name}\n"
            f"        FOREIGN KEY ({fk.column})\n"
            f"        REFERENCES {fk.ref_table}({fk.ref_column})\n"
            f"        ON DELETE {fk.on_delete}"
        )
    body = ",\n".join(f"    {line}" for line in lines)
    sql = f"{dialect.create_table_opening(spec.table)} (\n{body}\n){dialect.collated_table_suffix()};\n"
    if not dialect.inline_indexes():
        for index in spec.indexes:
            sql += dialect.create_index_sql(spec.table, index.name, ", ".join(index.columns)) + "\n"
    return sql
