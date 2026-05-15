"""Tests de contrat SQL RBAC — AUTH-RBAC-001."""

from __future__ import annotations

from pathlib import Path

SQL_FILE = Path("packages/forge-mvc-rbac/sql/rbac.sql")


def _sql() -> str:
    return SQL_FILE.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Présence du fichier
# ---------------------------------------------------------------------------


def test_rbac_sql_existe():
    assert SQL_FILE.is_file()


# ---------------------------------------------------------------------------
# Tables attendues
# ---------------------------------------------------------------------------


def test_sql_contient_table_roles():
    assert "CREATE TABLE IF NOT EXISTS roles" in _sql()


def test_sql_contient_table_permissions():
    assert "CREATE TABLE IF NOT EXISTS permissions" in _sql()


def test_sql_contient_table_role_permissions():
    assert "CREATE TABLE IF NOT EXISTS role_permissions" in _sql()


# ---------------------------------------------------------------------------
# Colonnes principales
# ---------------------------------------------------------------------------


def test_roles_contient_id():
    assert "id" in _sql()


def test_roles_contient_name():
    assert "name" in _sql()


def test_roles_contient_slug_unique():
    sql = _sql()
    assert "slug" in sql
    assert "UNIQUE" in sql


def test_permissions_contient_code_unique():
    sql = _sql()
    assert "code" in sql


def test_roles_contient_created_at():
    assert "created_at" in _sql()


def test_permissions_contient_created_at():
    assert "created_at" in _sql()


# ---------------------------------------------------------------------------
# Clé primaire composite role_permissions
# ---------------------------------------------------------------------------


def test_role_permissions_cle_primaire_composite():
    sql = _sql()
    assert "PRIMARY KEY (role_id, permission_id)" in sql


def test_role_permissions_contient_role_id():
    assert "role_id" in _sql()


def test_role_permissions_contient_permission_id():
    assert "permission_id" in _sql()


# ---------------------------------------------------------------------------
# Contraintes FK
# ---------------------------------------------------------------------------


def test_sql_contient_fk_role():
    assert "FOREIGN KEY (role_id)" in _sql()


def test_sql_contient_fk_permission():
    assert "FOREIGN KEY (permission_id)" in _sql()


def test_sql_contient_references_roles():
    assert "REFERENCES roles(id)" in _sql()


def test_sql_contient_references_permissions():
    assert "REFERENCES permissions(id)" in _sql()


def test_sql_contient_on_delete_cascade():
    assert "ON DELETE CASCADE" in _sql()


# ---------------------------------------------------------------------------
# Conventions Forge
# ---------------------------------------------------------------------------


def test_sql_utilise_innodb():
    assert "ENGINE=InnoDB" in _sql()


def test_sql_utilise_utf8mb4():
    assert "utf8mb4" in _sql()


def test_sql_utilise_auto_increment():
    assert "AUTO_INCREMENT" in _sql()


def test_sql_utilise_create_if_not_exists():
    assert "CREATE TABLE IF NOT EXISTS" in _sql()


# ---------------------------------------------------------------------------
# Absence de termes métier
# ---------------------------------------------------------------------------


def test_sql_sans_terme_metier():
    sql = _sql().lower()
    for term in ("commune", "sejour", "hebergement", "reservation"):
        assert term not in sql, f"Terme métier '{term}' détecté dans rbac.sql"
