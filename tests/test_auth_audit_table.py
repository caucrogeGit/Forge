"""Tests AUTH-AUDIT-001 — table SQL auth_audit_log."""

from __future__ import annotations

from pathlib import Path

from cli.security.auth import AUTH_AUDIT_LOG_SQL, cmd_auth_init


SQL_FILE = Path("tests/fixtures/app/mvc/models/sql/auth_audit_log.sql")


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


def test_auth_audit_log_sql_existe():
    assert SQL_FILE.exists()


def test_auth_audit_log_sql_contient_create_table():
    assert "CREATE TABLE IF NOT EXISTS auth_audit_log" in SQL_FILE.read_text(encoding="utf-8")


def test_auth_audit_log_sql_contient_colonnes_requises():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))

    assert "event_type VARCHAR(120) NOT NULL" in sql
    assert "user_id INT NULL" in sql
    assert "actor_user_id INT NULL" in sql
    assert "ip_address VARCHAR(45) NULL" in sql
    assert "user_agent VARCHAR(255) NULL" in sql
    assert "metadata_json TEXT NULL" in sql
    assert "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP" in sql


def test_auth_audit_log_sql_contient_index_event_type():
    assert "idx_auth_audit_log_event_type" in SQL_FILE.read_text(encoding="utf-8")


def test_auth_audit_log_sql_contient_index_user_id():
    assert "idx_auth_audit_log_user_id" in SQL_FILE.read_text(encoding="utf-8")


def test_auth_audit_log_sql_contient_index_actor_user_id():
    assert "idx_auth_audit_log_actor_user_id" in SQL_FILE.read_text(encoding="utf-8")


def test_auth_audit_log_sql_contient_index_created_at():
    assert "idx_auth_audit_log_created_at" in SQL_FILE.read_text(encoding="utf-8")


def test_auth_audit_log_sql_contient_fk_user_id_vers_users():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))

    assert "CONSTRAINT fk_auth_audit_log_user_id FOREIGN KEY (user_id) REFERENCES users(id)" in sql


def test_auth_audit_log_sql_contient_fk_actor_user_id_vers_users():
    sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))

    assert "CONSTRAINT fk_auth_audit_log_actor_user_id FOREIGN KEY (actor_user_id) REFERENCES users(id)" in sql


def test_auth_audit_log_sql_constant_correspond_au_fichier():
    assert SQL_FILE.read_text(encoding="utf-8") == AUTH_AUDIT_LOG_SQL


def test_auth_init_cree_auth_audit_log_sql(tmp_path):
    cmd_auth_init([], root=tmp_path)

    sql_file = tmp_path / "mvc" / "models" / "sql" / "auth_audit_log.sql"
    assert sql_file.exists()
    assert sql_file.read_text(encoding="utf-8") == AUTH_AUDIT_LOG_SQL


def test_auth_init_preserve_auth_audit_log_sql_existant(tmp_path, capsys):
    sql_dir = tmp_path / "mvc" / "models" / "sql"
    sql_dir.mkdir(parents=True)
    sql_file = sql_dir / "auth_audit_log.sql"
    sql_file.write_text("-- custom audit", encoding="utf-8")

    cmd_auth_init([], root=tmp_path)

    stdout = capsys.readouterr().out
    assert "PRÉSERVÉ" in stdout
    assert sql_file.read_text(encoding="utf-8") == "-- custom audit"


def test_auth_init_ne_cree_pas_evenement_reel(tmp_path):
    cmd_auth_init([], root=tmp_path)
    generated = "\n".join(
        path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    )

    assert "INSERT INTO auth_audit_log" not in generated
    assert "login.success" not in generated
    assert "login.failed" not in generated
