"""Tests AUTH-MFA-001 — table auth_mfa_factors et forge auth:init.

Les invariants de colonnes étaient auparavant vérifiés sur
`packages/forge-mvc-mfa/sql/auth_mfa_factors.sql`, un fichier que plus aucun
code ne lisait et qui doublonnait la spécification dialectale de
`cli/security/auth_sql.py`. Ce fichier est supprimé
(`OPTIN-DDL-DEAD-SQL-CLEANUP-001`) ; les mêmes invariants sont désormais
vérifiés sur le **rendu réel**, ce qui teste la source et non une copie.
"""

from __future__ import annotations

import pathlib

import pytest

from cli.security.auth import AUTH_MFA_FACTORS_SQL, cmd_auth_init
from cli.security.auth_sql import render_auth_sql

pytest.importorskip("forge_mvc_mariadb")

from forge_mvc_mariadb.dialect import MariaDBDialect  # noqa: E402


def _source_sql() -> str:
    """DDL rendu pour MariaDB, dialecte historique de ces garde-fous."""
    return render_auth_sql("auth_mfa_factors", MariaDBDialect())


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


# ---------------------------------------------------------------------------
# Fichier SQL auth_mfa_factors
# ---------------------------------------------------------------------------


def test_auth_mfa_factors_sql_source_is_the_dialectal_spec():
    """Le fichier .sql doublon est supprime : la source est auth_sql.py."""
    assert not pathlib.Path("packages/forge-mvc-mfa/sql").exists()
    assert "auth_mfa_factors" in _source_sql()


def test_auth_mfa_factors_sql_contains_create_table():
    sql = _source_sql()
    assert "CREATE TABLE IF NOT EXISTS auth_mfa_factors" in sql


def test_auth_mfa_factors_sql_contains_user_id():
    sql = _normalized(_source_sql())
    assert "user_id INT NOT NULL" in sql


def test_auth_mfa_factors_sql_contains_factor_type():
    sql = _normalized(_source_sql())
    assert "factor_type VARCHAR(40) NOT NULL" in sql


def test_auth_mfa_factors_sql_contains_totp_secret():
    sql = _normalized(_source_sql())
    assert "totp_secret VARCHAR(255) NOT NULL" in sql


def test_auth_mfa_factors_sql_contains_status_with_default():
    sql = _normalized(_source_sql())
    assert "status VARCHAR(40) NOT NULL DEFAULT 'pending'" in sql


def test_auth_mfa_factors_sql_contains_confirmed_at_null():
    sql = _normalized(_source_sql())
    assert "confirmed_at DATETIME NULL" in sql


def test_auth_mfa_factors_sql_contains_last_used_at_null():
    sql = _normalized(_source_sql())
    assert "last_used_at DATETIME NULL" in sql


def test_auth_mfa_factors_sql_contains_fk_to_users():
    sql = _normalized(_source_sql())
    assert "REFERENCES users(id)" in sql


def test_auth_mfa_factors_sql_contains_index_user_id():
    sql = _source_sql()
    assert "idx_auth_mfa_factors_user_id" in sql


def test_auth_mfa_factors_sql_contains_index_user_status():
    sql = _source_sql()
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
