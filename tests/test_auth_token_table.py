"""Tests AUTH-TOKEN-001 — table auth_tokens et forge auth:init."""

from __future__ import annotations

from pathlib import Path

from cli.security.auth import AUTH_TOKENS_SQL, USERS_SQL, cmd_auth_init


SQL_FILE = Path("tests/fixtures/app/mvc/models/sql/auth_tokens.sql")


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


# ---------------------------------------------------------------------------
# Fichier SQL auth_tokens
# ---------------------------------------------------------------------------


def test_auth_tokens_sql_file_exists():
    assert SQL_FILE.exists()


def test_auth_tokens_sql_contains_create_table():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS auth_tokens" in sql


def test_auth_tokens_sql_contains_user_id():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "user_id INT NOT NULL" in sql


def test_auth_tokens_sql_contains_purpose():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "purpose VARCHAR(80) NOT NULL" in sql


def test_auth_tokens_sql_contains_token_hash_unique():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "token_hash CHAR(64) NOT NULL UNIQUE" in sql


def test_auth_tokens_sql_contains_expires_at():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "expires_at DATETIME NOT NULL" in sql


def test_auth_tokens_sql_contains_used_at_null():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "used_at DATETIME NULL" in sql


def test_auth_tokens_sql_contains_created_at():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "created_at" in sql


def test_auth_tokens_sql_contains_index_user_purpose():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "idx_auth_tokens_user_purpose" in sql


def test_auth_tokens_sql_contains_index_expires_at():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "idx_auth_tokens_expires_at" in sql


def test_auth_tokens_sql_contains_fk_to_users():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "REFERENCES users(id)" in sql


# ---------------------------------------------------------------------------
# forge auth:init — creation et preservation
# ---------------------------------------------------------------------------


def test_auth_init_creates_users_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    users_file = tmp_path / "mvc" / "models" / "sql" / "users.sql"
    assert users_file.exists()
    assert users_file.read_text(encoding="utf-8") == USERS_SQL


def test_auth_init_creates_auth_tokens_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    tokens_file = tmp_path / "mvc" / "models" / "sql" / "auth_tokens.sql"
    assert tokens_file.exists()
    assert tokens_file.read_text(encoding="utf-8") == AUTH_TOKENS_SQL


def test_auth_init_preserves_existing_users_sql(tmp_path, capsys):
    sql_file = tmp_path / "mvc" / "models" / "sql" / "users.sql"
    sql_file.parent.mkdir(parents=True)
    sql_file.write_text("-- custom users", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    out, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in out
    assert sql_file.read_text(encoding="utf-8") == "-- custom users"


def test_auth_init_preserves_existing_auth_tokens_sql(tmp_path, capsys):
    sql_dir = tmp_path / "mvc" / "models" / "sql"
    sql_dir.mkdir(parents=True)
    tokens_file = sql_dir / "auth_tokens.sql"
    tokens_file.write_text("-- custom tokens", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    out, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in out
    assert tokens_file.read_text(encoding="utf-8") == "-- custom tokens"


def test_auth_init_does_not_create_real_token(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated = "\n".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file())
    assert "INSERT INTO auth_tokens" not in generated
    assert "token_urlsafe" not in generated


def test_auth_tokens_sql_constant_contains_create_table():
    assert "CREATE TABLE IF NOT EXISTS auth_tokens" in AUTH_TOKENS_SQL


def test_auth_tokens_sql_constant_contains_token_hash_char64():
    assert "token_hash CHAR(64)" in AUTH_TOKENS_SQL
