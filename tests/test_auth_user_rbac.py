"""Tests AUTH-USER-RBAC-001 — association optionnelle user_roles."""

from __future__ import annotations

import inspect
from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    AuthUserRole,
    auth_user_role_key,
    auth_user_roles_match,
    create_auth_user_role,
    is_valid_auth_user_role,
    normalize_auth_user_role,
    user_role_key,
    validate_user_role_role_id,
    validate_user_role_user_id,
)
from core.auth.exceptions import InvalidAuthUserError
from cli.security.auth import USER_ROLES_SQL, cmd_auth_init


SQL_FILE = Path("packages/forge-mvc-rbac/sql/user_roles.sql")


def _normalized(sql: str) -> str:
    return " ".join(sql.split())


class TestAuthUserRoleContract:
    def test_creates_valid_association(self):
        association = AuthUserRole(user_id=1, role_id=2)

        assert association.user_id == 1
        assert association.role_id == 2
        assert association.created_at is None

    def test_create_helper_returns_association(self):
        association = create_auth_user_role(1, 2, created_at="now")

        assert association == AuthUserRole(user_id=1, role_id=2, created_at="now")

    def test_normalize_from_dict(self):
        association = normalize_auth_user_role({
            "user_id": 1,
            "role_id": 2,
            "created_at": "2026-05-05 12:00:00",
        })

        assert association.user_id == 1
        assert association.role_id == 2
        assert association.created_at == "2026-05-05 12:00:00"

    def test_refuses_zero_user_id(self):
        with pytest.raises(InvalidAuthUserError):
            validate_user_role_user_id(0)

    def test_refuses_negative_user_id(self):
        with pytest.raises(InvalidAuthUserError):
            validate_user_role_user_id(-1)

    def test_refuses_bool_user_id(self):
        with pytest.raises(InvalidAuthUserError):
            validate_user_role_user_id(True)

    def test_refuses_zero_role_id(self):
        with pytest.raises(InvalidAuthUserError):
            validate_user_role_role_id(0)

    def test_refuses_negative_role_id(self):
        with pytest.raises(InvalidAuthUserError):
            validate_user_role_role_id(-1)

    def test_refuses_bool_role_id(self):
        with pytest.raises(InvalidAuthUserError):
            validate_user_role_role_id(False)

    def test_stable_key_from_ids(self):
        assert user_role_key(1, 2) == "1:2"

    def test_stable_key_from_association(self):
        assert auth_user_role_key(AuthUserRole(user_id=1, role_id=2)) == "1:2"

    def test_logical_comparison_matches_same_pair(self):
        left = AuthUserRole(user_id=1, role_id=2)
        right = AuthUserRole(user_id=1, role_id=2)

        assert auth_user_roles_match(left, right) is True

    def test_logical_comparison_rejects_different_user(self):
        left = AuthUserRole(user_id=1, role_id=2)
        right = AuthUserRole(user_id=3, role_id=2)

        assert auth_user_roles_match(left, right) is False

    def test_logical_comparison_rejects_different_role(self):
        left = AuthUserRole(user_id=1, role_id=2)
        right = AuthUserRole(user_id=1, role_id=3)

        assert auth_user_roles_match(left, right) is False

    def test_is_valid_requires_auth_user_role_instance(self):
        association = AuthUserRole(user_id=1, role_id=2)

        assert is_valid_auth_user_role(association) is True
        assert is_valid_auth_user_role({"user_id": 1, "role_id": 2}) is False


class TestUserRolesSql:
    def test_sql_file_exists(self):
        assert SQL_FILE.exists()

    def test_sql_contains_create_table(self):
        sql = SQL_FILE.read_text(encoding="utf-8")
        assert "CREATE TABLE IF NOT EXISTS user_roles" in sql

    def test_sql_contains_required_columns(self):
        sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))

        assert "user_id INT NOT NULL" in sql
        assert "role_id INT NOT NULL" in sql
        assert "created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP" in sql

    def test_sql_contains_primary_key_user_role(self):
        sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
        assert "PRIMARY KEY (user_id, role_id)" in sql

    def test_sql_contains_user_index(self):
        sql = SQL_FILE.read_text(encoding="utf-8")
        assert "idx_user_roles_user_id" in sql

    def test_sql_contains_role_index(self):
        sql = SQL_FILE.read_text(encoding="utf-8")
        assert "idx_user_roles_role_id" in sql

    def test_sql_contains_fk_to_users(self):
        sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
        assert "REFERENCES users(id)" in sql

    def test_sql_contains_fk_to_roles(self):
        sql = _normalized(SQL_FILE.read_text(encoding="utf-8"))
        assert "REFERENCES roles(id)" in sql

    def test_sql_constant_matches_file(self):
        assert SQL_FILE.read_text(encoding="utf-8") == USER_ROLES_SQL


class TestAuthInitUserRoles:
    def test_auth_init_creates_user_roles_sql(self, tmp_path):
        cmd_auth_init([], root=tmp_path)

        sql_file = tmp_path / "mvc" / "models" / "sql" / "user_roles.sql"
        assert sql_file.exists()
        assert sql_file.read_text(encoding="utf-8") == USER_ROLES_SQL

    def test_auth_init_preserves_existing_user_roles_sql(self, tmp_path, capsys):
        sql_dir = tmp_path / "mvc" / "models" / "sql"
        sql_dir.mkdir(parents=True)
        sql_file = sql_dir / "user_roles.sql"
        sql_file.write_text("-- custom user roles", encoding="utf-8")

        cmd_auth_init([], root=tmp_path)

        out, _ = capsys.readouterr()
        assert "diffère" in out  # WARNED : contenu divergent (CLI-SCAFFOLD-PRIMITIVE-001)
        assert sql_file.read_text(encoding="utf-8") == "-- custom user roles"

    def test_auth_init_does_not_seed_roles_or_permissions(self, tmp_path):
        cmd_auth_init([], root=tmp_path)
        generated = "\n".join(
            p.read_text(encoding="utf-8")
            for p in tmp_path.rglob("*")
            if p.is_file()
        )

        assert "INSERT INTO user_roles" not in generated
        assert "INSERT INTO roles" not in generated
        assert "INSERT INTO permissions" not in generated


class TestAuthUserRbacBoundaries:
    def test_module_has_no_sql_engine_dependency(self):
        import forge_mvc_rbac.user_rbac as module

        source = inspect.getsource(module)
        for forbidden in ("mysql", "pymysql", "sqlite", "connect(", "execute("):
            assert forbidden not in source

    def test_module_does_not_import_rbac_permissions(self):
        import forge_mvc_rbac.user_rbac as module

        source = inspect.getsource(module)
        assert "Permission" not in source
        assert "require_permission" not in source
        assert "has_permission" not in source
        assert "can(" not in source

    def test_auth_user_role_has_no_permission_fields(self):
        association = AuthUserRole(user_id=1, role_id=2)

        assert not hasattr(association, "permission_id")
        assert not hasattr(association, "permissions")
        assert not hasattr(association, "can")
