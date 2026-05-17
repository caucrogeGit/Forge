"""Tests RBAC-EXTRACT-001 : RBAC déplacé dans forge-mvc-rbac."""
from __future__ import annotations

from pathlib import Path

import pytest
pytest.importorskip("forge_mvc_rbac")

pytestmark = pytest.mark.meta


class TestRbacModuleAvailable:
    def test_can_import_public_api(self):
        from forge_mvc_rbac import (  # noqa: F401
            AuthJinjaUser,
            AuthUserRbacResolverError,
            AuthUserRole,
            FetchAll,
            Permission,
            PermissionDenied,
            RbacValidationError,
            Role,
            auth_user_can,
            auth_user_role_key,
            auth_user_roles_match,
            create_auth_user_role,
            get_jinja_current_user,
            get_request_permissions,
            get_user_permissions,
            get_user_role_ids,
            has_permission,
            is_valid_auth_user_role,
            make_auth_jinja_can,
            make_auth_jinja_context,
            make_can,
            normalize_auth_user_role,
            normalize_permission_code,
            normalize_role_slug,
            require_permission,
            require_user_permission,
            sanitize_jinja_user,
            user_has_permission,
            user_role_key,
            validate_auth_user_role_contract,
            validate_permission,
            validate_role,
            validate_user_role_role_id,
            validate_user_role_user_id,
        )
        assert Role is not None

    def test_module_has_version(self):
        import forge_mvc_rbac
        assert hasattr(forge_mvc_rbac, "__version__")
        assert forge_mvc_rbac.__version__ == "1.0.0b4"

    def test_all_exports_complete(self):
        import forge_mvc_rbac
        expected = {
            "Role", "Permission", "RbacValidationError", "PermissionDenied",
            "has_permission", "require_permission", "make_can",
            "normalize_permission_code", "normalize_role_slug",
            "validate_permission", "validate_role", "get_request_permissions",
            "AuthUserRole", "auth_user_role_key", "auth_user_roles_match",
            "create_auth_user_role", "is_valid_auth_user_role",
            "normalize_auth_user_role", "user_role_key",
            "validate_auth_user_role_contract",
            "validate_user_role_role_id", "validate_user_role_user_id",
            "AuthUserRbacResolverError", "FetchAll",
            "get_user_permissions", "get_user_role_ids", "user_has_permission",
            "auth_user_can", "require_user_permission",
            "AuthJinjaUser", "get_jinja_current_user",
            "make_auth_jinja_can", "make_auth_jinja_context", "sanitize_jinja_user",
        }
        assert expected.issubset(set(forge_mvc_rbac.__all__))


class TestRbacRemovedFromCore:
    @pytest.mark.parametrize("removed_path", [
        "core/security/rbac.py",
        "core/auth/authorization.py",
        "core/auth/user_rbac.py",
        "core/auth/user_rbac_resolver.py",
        "core/auth/jinja.py",
        "mvc/models/sql/rbac.sql",
        "mvc/models/sql/user_roles.sql",
    ])
    def test_path_removed(self, removed_path):
        assert not Path(removed_path).exists(), (
            f"{removed_path} aurait dû être supprimé"
        )

    def test_old_import_fails(self):
        with pytest.raises(ImportError):
            import core.security.rbac  # noqa: F401


class TestSqlMovedToModule:
    @pytest.mark.parametrize("sql_file", ["rbac.sql", "user_roles.sql"])
    def test_sql_in_module(self, sql_file):
        sql_path = Path(f"packages/forge-mvc-rbac/sql/{sql_file}")
        assert sql_path.exists(), f"{sql_file} doit être dans packages/forge-mvc-rbac/sql/"


class TestNoCoreRbacImportsRemain:
    @pytest.mark.parametrize("forbidden_import", [
        "from core.security.rbac",
        "import core.security.rbac",
        "from core.auth.authorization",
        "from core.auth.user_rbac",
        "from core.auth.jinja",
        "import core.auth.authorization",
    ])
    def test_no_forbidden_imports(self, forbidden_import):
        this_file = Path(__file__).resolve()
        roots = [Path("core"), Path("mvc"), Path("forge_cli"), Path("tests"), Path("integrations")]
        offenders = []
        for root in roots:
            if not root.exists():
                continue
            for py_file in root.rglob("*.py"):
                if py_file.resolve() == this_file:
                    continue
                content = py_file.read_text(encoding="utf-8")
                if forbidden_import in content:
                    offenders.append(str(py_file))
        assert not offenders, (
            f"Imports RBAC core restants dans : {offenders}"
        )


class TestRbacFunctional:
    def test_role_creation_et_validation(self):
        from forge_mvc_rbac import Role, normalize_role_slug, validate_role
        slug = normalize_role_slug("Super Admin")
        assert slug == "super-admin"
        validate_role("Super Admin", slug)
        role = Role(id=None, name="Super Admin", slug=slug)
        assert role.slug == "super-admin"

    def test_permission_creation_et_validation(self):
        from forge_mvc_rbac import Permission, normalize_permission_code, validate_permission
        code = normalize_permission_code("Posts Edit")
        assert code == "posts.edit"
        validate_permission(code)
        perm = Permission(id=None, code=code)
        assert perm.code == "posts.edit"

    def test_user_role_association(self):
        from forge_mvc_rbac import AuthUserRole, create_auth_user_role, auth_user_roles_match
        assoc = create_auth_user_role(1, 2)
        assert assoc.user_id == 1
        assert assoc.role_id == 2
        assert auth_user_roles_match(assoc, AuthUserRole(user_id=1, role_id=2))

    def test_user_has_permission_stub(self):
        from forge_mvc_rbac import user_has_permission

        def fetch(sql, params):
            return [{"code": "posts.edit"}]

        assert user_has_permission(1, "posts.edit", fetch_all=fetch) is True
        assert user_has_permission(1, "posts.delete", fetch_all=fetch) is False


class TestPyprojectMetadata:
    def test_pyproject_version(self):
        content = Path("packages/forge-mvc-rbac/pyproject.toml").read_text(encoding="utf-8")
        assert 'version = "1.0.0b4"' in content

    def test_description_updated(self):
        content = Path("packages/forge-mvc-rbac/pyproject.toml").read_text(encoding="utf-8")
        assert "placeholder" not in content.lower()

    def test_beta_status(self):
        content = Path("packages/forge-mvc-rbac/pyproject.toml").read_text(encoding="utf-8")
        assert "4 - Beta" in content
