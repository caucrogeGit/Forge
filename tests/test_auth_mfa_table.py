"""Tests AUTH-MFA-001 — table auth_mfa_factors et forge auth:init."""

from __future__ import annotations

from pathlib import Path

from cli.security.auth import AUTH_MFA_FACTORS_SQL, cmd_auth_init


SQL_FILE = Path("packages/forge-mvc-mfa/sql/auth_mfa_factors.sql")


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


# ---------------------------------------------------------------------------
# Fichier SQL auth_mfa_factors
# ---------------------------------------------------------------------------


def test_auth_mfa_factors_sql_file_exists():
    assert SQL_FILE.exists()


def test_auth_mfa_factors_sql_contains_create_table():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "CREATE TABLE IF NOT EXISTS auth_mfa_factors" in sql


def test_auth_mfa_factors_sql_contains_user_id():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "user_id INT NOT NULL" in sql


def test_auth_mfa_factors_sql_contains_factor_type():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "factor_type VARCHAR(40) NOT NULL" in sql


def test_auth_mfa_factors_sql_contains_totp_secret():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "totp_secret VARCHAR(255) NOT NULL" in sql


def test_auth_mfa_factors_sql_contains_status_with_default():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "status VARCHAR(40) NOT NULL DEFAULT 'pending'" in sql


def test_auth_mfa_factors_sql_contains_confirmed_at_null():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "confirmed_at DATETIME NULL" in sql


def test_auth_mfa_factors_sql_contains_last_used_at_null():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "last_used_at DATETIME NULL" in sql


def test_auth_mfa_factors_sql_contains_fk_to_users():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
    assert "REFERENCES users(id)" in sql


def test_auth_mfa_factors_sql_contains_index_user_id():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "idx_auth_mfa_factors_user_id" in sql


def test_auth_mfa_factors_sql_contains_index_user_status():
    sql = SQL_FILE.read_text(encoding="utf-8")
    assert "idx_auth_mfa_factors_user_status" in sql


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
    mfa_file = tmp_path / "mvc" / "models" / "sql" / "auth_mfa_factors.sql"
    assert mfa_file.exists()
    assert mfa_file.read_text(encoding="utf-8") == AUTH_MFA_FACTORS_SQL


def test_auth_init_preserves_existing_auth_mfa_factors_sql(tmp_path, capsys):
    sql_dir = tmp_path / "mvc" / "models" / "sql"
    sql_dir.mkdir(parents=True)
    mfa_file = sql_dir / "auth_mfa_factors.sql"
    mfa_file.write_text("-- custom mfa", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    out, _ = capsys.readouterr()
    assert "diffère" in out  # WARNED : contenu divergent (CLI-SCAFFOLD-PRIMITIVE-001)
    assert mfa_file.read_text(encoding="utf-8") == "-- custom mfa"


def test_auth_init_does_not_create_real_mfa_factor(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated = "\n".join(p.read_text(encoding="utf-8") for p in tmp_path.rglob("*") if p.is_file())
    assert "INSERT INTO auth_mfa_factors" not in generated
    assert "pyotp" not in generated


def test_auth_mfa_factors_sql_constant_contains_create_table():
    assert "CREATE TABLE IF NOT EXISTS auth_mfa_factors" in AUTH_MFA_FACTORS_SQL


def test_auth_mfa_factors_sql_constant_contains_totp_secret():
    assert "totp_secret VARCHAR(255) NOT NULL" in AUTH_MFA_FACTORS_SQL
