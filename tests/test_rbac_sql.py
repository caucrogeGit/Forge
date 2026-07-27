"""Tests de contrat SQL RBAC — AUTH-RBAC-001.

Ces garde-fous portaient sur `packages/forge-mvc-rbac/sql/rbac.sql`, fichier
non livre dans le wheel, lu par aucun code, et dont certains tests EXIGEAIENT
des constructions propres a MariaDB (AUTO_INCREMENT, InnoDB, utf8mb4) : ils
verrouillaient donc le defaut mesure par OPTIN-DDL-DIALECT-AUDIT-001.

Le fichier est remplace par la declaration `forge_mvc_rbac.tables`, rendue par
`forge rbac:init` pour le backend installe (OPTIN-DDL-RBAC-INIT-001). Les
invariants de MODELE sont conserves et verifies sur le rendu MariaDB, ou
AUTO_INCREMENT et InnoDB restent legitimes ; un controle de portabilite est
ajoute pour les trois autres backends.
"""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("forge_mvc_rbac")
pytest.importorskip("forge_mvc_mariadb")

from core.database.table_ddl import render_create_table  # noqa: E402
from forge_mvc_mariadb.dialect import MariaDBDialect  # noqa: E402


def _sql() -> str:
    """DDL rendu des trois tables RBAC, dialecte MariaDB (historique)."""
    from forge_mvc_rbac.tables import MIGRATIONS

    dialect = MariaDBDialect()
    return "\n".join(
        stmt for _name, table in MIGRATIONS for stmt in render_create_table(table, dialect)
    )


# ---------------------------------------------------------------------------
# Présence du fichier
# ---------------------------------------------------------------------------


def test_rbac_sql_source_est_la_declaration():
    assert not Path("packages/forge-mvc-rbac/sql/rbac.sql").exists()
    from forge_mvc_rbac.tables import MIGRATIONS

    assert [t.name for _f, t in MIGRATIONS] == ["roles", "permissions", "role_permissions"]


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


# ---------------------------------------------------------------------------
# Portabilite : le defaut mesure par l'audit ne doit pas revenir
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("backend_name", ["sqlite", "postgres", "mssql"])
def test_rendu_portable_hors_mariadb(backend_name: str) -> None:
    pytest.importorskip(f"forge_mvc_{backend_name}")
    from forge_mvc_rbac.tables import MIGRATIONS

    module = __import__(f"forge_mvc_{backend_name}.dialect", fromlist=["dialect"])
    dialect_cls = next(
        value for key, value in vars(module).items()
        if key.endswith("Dialect") and isinstance(value, type)
    )
    dialect = dialect_cls()
    sql = "\n".join(
        stmt for _name, table in MIGRATIONS for stmt in render_create_table(table, dialect)
    ).upper()
    for marker in ("AUTO_INCREMENT", "UNSIGNED", "ENGINE=", "INNODB", "UTF8MB4"):
        assert marker not in sql, f"{backend_name} : DDL RBAC contenant {marker}"
