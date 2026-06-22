"""Tests AUTH-RATE-LIMIT-001 — table SQL auth_rate_limit_attempts."""

from __future__ import annotations

from pathlib import Path

from cli.auth import AUTH_RATE_LIMIT_ATTEMPTS_SQL, cmd_auth_init


SQL_FILE = Path("mvc/models/sql/auth_rate_limit_attempts.sql")


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


def test_auth_rate_limit_attempts_sql_existe():
    assert SQL_FILE.exists()


def test_auth_rate_limit_attempts_sql_contient_create_table():
    sql = SQL_FILE.read_text(encoding="utf-8")

    assert "CREATE TABLE IF NOT EXISTS auth_rate_limit_attempts" in sql


def test_auth_rate_limit_attempts_sql_contient_colonnes_requises():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))

    assert "action VARCHAR(120) NOT NULL" in sql
    assert "rate_key VARCHAR(255) NOT NULL" in sql
    assert "ip_address VARCHAR(45) NULL" in sql
    assert "user_id INT NULL" in sql
    assert "success BOOLEAN NOT NULL DEFAULT FALSE" in sql
    assert "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP" in sql


def test_auth_rate_limit_attempts_sql_contient_index_action_rate_key():
    sql = SQL_FILE.read_text(encoding="utf-8")

    assert "idx_auth_rate_limit_action_key" in sql


def test_auth_rate_limit_attempts_sql_contient_index_created_at():
    sql = SQL_FILE.read_text(encoding="utf-8")

    assert "idx_auth_rate_limit_created_at" in sql


def test_auth_rate_limit_attempts_sql_contient_fk_users():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))

    assert "CONSTRAINT fk_auth_rate_limit_user_id FOREIGN KEY (user_id) REFERENCES users(id)" in sql


def test_auth_rate_limit_attempts_sql_constant_correspond_au_fichier():
    assert SQL_FILE.read_text(encoding="utf-8") == AUTH_RATE_LIMIT_ATTEMPTS_SQL


def test_auth_init_cree_auth_rate_limit_attempts_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)

    sql_file = tmp_path / "mvc" / "models" / "sql" / "auth_rate_limit_attempts.sql"
    assert sql_file.exists()
    assert sql_file.read_text(encoding="utf-8") == AUTH_RATE_LIMIT_ATTEMPTS_SQL


def test_auth_init_preserve_auth_rate_limit_attempts_sql_existant(tmp_path, capsys):
    sql_dir = tmp_path / "mvc" / "models" / "sql"
    sql_dir.mkdir(parents=True)
    sql_file = sql_dir / "auth_rate_limit_attempts.sql"
    sql_file.write_text("-- custom rate limit", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    stdout = capsys.readouterr().out
    assert "PRÉSERVÉ" in stdout
    assert sql_file.read_text(encoding="utf-8") == "-- custom rate limit"


def test_auth_init_ne_cree_pas_tentative_reelle(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated = "\n".join(
        path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    )

    assert "INSERT INTO auth_rate_limit_attempts" not in generated
    assert "INSERT INTO users" not in generated
    assert "login.failed" not in generated
