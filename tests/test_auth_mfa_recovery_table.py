"""Tests AUTH-MFA-003 — table auth_mfa_recovery_codes et forge auth:init."""

from __future__ import annotations

from pathlib import Path

from forge_cli.auth import AUTH_MFA_RECOVERY_CODES_SQL, cmd_auth_init


SQL_FILE = Path("packages/forge-mvc-mfa/sql/auth_mfa_recovery_codes.sql")


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


# ---------------------------------------------------------------------------
# Fichier SQL auth_mfa_recovery_codes
# ---------------------------------------------------------------------------


def test_auth_mfa_recovery_codes_sql_file_exists():
    assert SQL_FILE.exists()


def test_auth_mfa_recovery_codes_sql_contains_create_table():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS auth_mfa_recovery_codes" in sql


def test_auth_mfa_recovery_codes_sql_contains_user_id():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "user_id INT NOT NULL" in sql


def test_auth_mfa_recovery_codes_sql_contains_code_hash():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "code_hash CHAR(64) NOT NULL UNIQUE" in sql


def test_auth_mfa_recovery_codes_sql_contains_used_at():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "used_at DATETIME NULL" in sql


def test_auth_mfa_recovery_codes_sql_contains_created_at():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "created_at" in sql


def test_auth_mfa_recovery_codes_sql_contains_updated_at():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "updated_at" in sql


def test_auth_mfa_recovery_codes_sql_contains_fk_to_users():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "REFERENCES users(id)" in sql


def test_auth_mfa_recovery_codes_sql_contains_index_user_id():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "idx_auth_mfa_recovery_codes_user_id" in sql


def test_auth_mfa_recovery_codes_sql_contains_index_used_at():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "idx_auth_mfa_recovery_codes_used_at" in sql


# ---------------------------------------------------------------------------
# forge auth:init — creation et preservation
# ---------------------------------------------------------------------------


def test_auth_init_creates_users_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    assert (tmp_path / "mvc" / "models" / "sql" / "users.sql").exists()


def test_auth_init_creates_auth_tokens_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    assert (tmp_path / "mvc" / "models" / "sql" / "auth_tokens.sql").exists()


def test_auth_init_creates_auth_mfa_factors_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    assert (tmp_path / "mvc" / "models" / "sql" / "auth_mfa_factors.sql").exists()


def test_auth_init_creates_auth_mfa_recovery_codes_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)
    recovery_file = tmp_path / "mvc" / "models" / "sql" / "auth_mfa_recovery_codes.sql"
    assert recovery_file.exists()
    assert recovery_file.read_text(encoding="utf-8") == AUTH_MFA_RECOVERY_CODES_SQL


def test_auth_init_preserves_existing_auth_mfa_recovery_codes_sql(tmp_path, capsys):
    sql_dir = tmp_path / "mvc" / "models" / "sql"
    sql_dir.mkdir(parents=True)
    recovery_file = sql_dir / "auth_mfa_recovery_codes.sql"
    recovery_file.write_text("-- custom recovery codes", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    out, _ = capsys.readouterr()
    assert "PRÉSERVÉ" in out
    assert recovery_file.read_text(encoding="utf-8") == "-- custom recovery codes"


def test_auth_init_does_not_generate_real_recovery_codes(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated = "\n".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file())
    assert "INSERT INTO auth_mfa_recovery_codes" not in generated
    assert "generate_recovery_code" not in generated
    assert "raw_codes" not in generated


def test_auth_mfa_recovery_codes_sql_constant_contains_create_table():
    assert "CREATE TABLE IF NOT EXISTS auth_mfa_recovery_codes" in AUTH_MFA_RECOVERY_CODES_SQL


def test_auth_mfa_recovery_codes_sql_constant_contains_code_hash():
    assert "code_hash CHAR(64) NOT NULL UNIQUE" in AUTH_MFA_RECOVERY_CODES_SQL
