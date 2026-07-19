"""AUTH-INIT-DIALECT-DDL-001 (ADR-084) : DDL Auth/User rendu par le dialecte.

Trois garde-fous :
- parité stricte : le rendu MariaDB de chaque table est STRICTEMENT égal à la
  constante canonique de cli.security.auth (source unique verrouillée) ;
- applicabilité SQLite : le rendu SQLite des 7 tables s'exécute réellement sur
  sqlite3 (:memory:), y compris les CREATE INDEX séparés ;
- refus explicite : sans backend BDD résolu, auth:init refuse en nommant
  l'ADR-084, au lieu d'émettre le SQL d'un autre dialecte.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_mariadb")
pytest.importorskip("forge_mvc_sqlite")
pytest.importorskip("forge_mvc_postgres")
pytest.importorskip("forge_mvc_mssql")

from cli.security import auth
from cli.security.auth import cmd_auth_init
from cli.security.auth_sql import AUTH_TABLE_SPECS, render_auth_sql
from forge_mvc_mariadb.dialect import MariaDBDialect
from forge_mvc_mssql.dialect import MSSQLDialect
from forge_mvc_postgres.dialect import PostgreSQLDialect
from forge_mvc_sqlite.dialect import SQLiteDialect


# Ordre de dépendance FK : users d'abord (roles est créée par le test).
CONSTANTS: dict[str, str] = {
    "users": auth.USERS_SQL,
    "auth_tokens": auth.AUTH_TOKENS_SQL,
    "auth_mfa_factors": auth.AUTH_MFA_FACTORS_SQL,
    "auth_mfa_recovery_codes": auth.AUTH_MFA_RECOVERY_CODES_SQL,
    "user_roles": auth.USER_ROLES_SQL,
    "auth_audit_log": auth.AUTH_AUDIT_LOG_SQL,
    "auth_rate_limit_attempts": auth.AUTH_RATE_LIMIT_ATTEMPTS_SQL,
}


def test_specs_couvrent_les_sept_fichiers_sql() -> None:
    # Les specs déclaratives couvrent exactement les fichiers de auth:init.
    filenames = {item.filename.removesuffix(".sql") for item in auth.AUTH_SQL_FILES}
    assert set(AUTH_TABLE_SPECS) == filenames == set(CONSTANTS)


@pytest.mark.parametrize(
    "method",
    [
        "auto_increment_primary_key_ddl",
        "char_type",
        "boolean_default_literal",
        "timestamp_default_clause",
        "collated_table_suffix",
    ],
)
def test_protocol_dialect_declare_les_traits_auth(method: str) -> None:
    # ADR-084 : les traits DDL Auth/User font partie du contrat Dialect.
    from core.database.backend import Dialect

    assert hasattr(Dialect, method)


# ── Parité stricte MariaDB : les constantes restent la source unique ──────────

@pytest.mark.parametrize("table_name", sorted(CONSTANTS))
def test_parite_stricte_rendu_mariadb_egal_constante(table_name: str) -> None:
    rendered = render_auth_sql(table_name, MariaDBDialect())
    assert rendered == CONSTANTS[table_name]


# ── Applicabilité SQLite : exécution réelle sur :memory: ─────────────────────

def _sqlite_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys = ON")
    # Prérequis RBAC : user_roles référence roles(id) (table de l'opt-in).
    conn.execute("CREATE TABLE roles (id INTEGER PRIMARY KEY AUTOINCREMENT, slug TEXT, name TEXT)")
    return conn


def test_rendu_sqlite_des_sept_tables_s_execute() -> None:
    conn = _sqlite_connection()
    try:
        for table_name in CONSTANTS:
            conn.executescript(render_auth_sql(table_name, SQLiteDialect()))
        tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert set(CONSTANTS) <= tables
    finally:
        conn.close()


def test_rendu_sqlite_cree_les_index_separes() -> None:
    conn = _sqlite_connection()
    try:
        for table_name in CONSTANTS:
            conn.executescript(render_auth_sql(table_name, SQLiteDialect()))
        indexes = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type = 'index'")}
        expected = {index.name for spec in AUTH_TABLE_SPECS.values() for index in spec.indexes}
        assert expected <= indexes
    finally:
        conn.close()


def test_rendu_sqlite_insertion_et_cascade_fonctionnent() -> None:
    # Preuve sémantique : FK CASCADE et défauts sont réellement actifs.
    conn = _sqlite_connection()
    try:
        for table_name in CONSTANTS:
            conn.executescript(render_auth_sql(table_name, SQLiteDialect()))
        conn.execute("INSERT INTO users (email, password_hash) VALUES ('a@b.com', 'hash')")
        conn.execute(
            "INSERT INTO auth_tokens (user_id, purpose, token_hash, expires_at) "
            "VALUES (1, 'reset', 'h', '2026-01-01 00:00:00')"
        )
        row = conn.execute("SELECT is_active, created_at FROM users").fetchone()
        assert row[0] == 1 and row[1] is not None
        conn.execute("DELETE FROM users")
        assert conn.execute("SELECT COUNT(*) FROM auth_tokens").fetchone()[0] == 0
    finally:
        conn.close()


# ── Jamais le SQL d'un autre dialecte (postgres/mssql) ────────────────────────

@pytest.mark.parametrize("table_name", sorted(CONSTANTS))
def test_rendus_postgres_et_mssql_sans_traits_mariadb(table_name: str) -> None:
    for dialect in (PostgreSQLDialect(), MSSQLDialect()):
        rendered = render_auth_sql(table_name, dialect)
        assert "AUTO_INCREMENT" not in rendered
        assert "ENGINE=" not in rendered
        assert "ON UPDATE CURRENT_TIMESTAMP" not in rendered


# ── cmd_auth_init : rendu via le backend actif ────────────────────────────────

def test_auth_init_rend_le_sql_sqlite_sous_backend_sqlite(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("DB_BACKEND", "sqlite")
    from core.database import backend as backend_module

    backend_module.reset_backend()
    try:
        cmd_auth_init([], root=tmp_path)
        users_sql = (tmp_path / "mvc" / "models" / "sql" / "users.sql").read_text(encoding="utf-8")
        assert "INTEGER PRIMARY KEY AUTOINCREMENT" in users_sql
        assert "ENGINE=InnoDB" not in users_sql
        assert "AUTO_INCREMENT PRIMARY KEY" not in users_sql
        # L'ensemble écrit est réellement applicable sur SQLite (users d'abord, FK).
        conn = _sqlite_connection()
        try:
            conn.executescript(users_sql)
            for name in ("auth_tokens", "auth_audit_log", "auth_rate_limit_attempts",
                         "auth_mfa_factors", "auth_mfa_recovery_codes", "user_roles"):
                path = tmp_path / "mvc" / "models" / "sql" / f"{name}.sql"
                if path.exists():
                    conn.executescript(path.read_text(encoding="utf-8"))
        finally:
            conn.close()
    finally:
        backend_module.reset_backend()


def test_auth_init_refuse_sans_backend_en_nommant_adr_084(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import core.database.backend as backend_module

    def _no_backend() -> object:
        raise RuntimeError("Aucun backend BDD installé.")

    monkeypatch.setattr(backend_module, "get_backend", _no_backend)
    with pytest.raises(SystemExit) as exc_info:
        cmd_auth_init([], root=tmp_path)
    message = str(exc_info.value)
    assert "ADR-084" in message
    assert "forge-mvc-mariadb" in message
    assert "forge-mvc-sqlite" in message
    # Refus net : aucun fichier SQL n'a été écrit.
    assert not (tmp_path / "mvc" / "models" / "sql").exists()
