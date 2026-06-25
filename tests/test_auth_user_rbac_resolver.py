"""Tests AUTH-USER-RBAC-002 — resolution des permissions RBAC utilisateur."""

from __future__ import annotations

import inspect

import pytest
pytest.importorskip("forge_mvc_rbac")

from forge_mvc_rbac import (
    AuthUserRbacResolverError,
    get_user_permissions,
    get_user_role_ids,
    user_has_permission,
)
from core.auth.exceptions import InvalidAuthUserError
from core.auth.user import AuthUser
from forge_mvc_rbac.resolver import (
    SELECT_USER_PERMISSIONS_SQL,
    SELECT_USER_ROLE_IDS_SQL,
)


class FakeFetchAll:
    def __init__(self, rows_by_sql: dict[str, list[dict]]):
        self.rows_by_sql = rows_by_sql
        self.calls: list[tuple[str, tuple]] = []

    def __call__(self, sql: str, params: tuple):
        self.calls.append((sql, params))
        return self.rows_by_sql.get(sql, [])


def test_get_user_role_ids_resolves_roles_for_user():
    fetch = FakeFetchAll({
        SELECT_USER_ROLE_IDS_SQL: [
            {"role_id": 2},
            {"role_id": 1},
        ],
    })

    assert get_user_role_ids(42, fetch_all=fetch) == (1, 2)
    assert fetch.calls == [(SELECT_USER_ROLE_IDS_SQL, (42,))]


def test_get_user_role_ids_removes_duplicates():
    fetch = FakeFetchAll({
        SELECT_USER_ROLE_IDS_SQL: [
            {"role_id": 2},
            {"role_id": 2},
            {"role_id": 1},
        ],
    })

    assert get_user_role_ids(42, fetch_all=fetch) == (1, 2)


def test_get_user_role_ids_user_without_role_returns_empty_tuple():
    fetch = FakeFetchAll({SELECT_USER_ROLE_IDS_SQL: []})

    assert get_user_role_ids(42, fetch_all=fetch) == ()


def test_get_user_role_ids_rejects_invalid_user_id():
    with pytest.raises(InvalidAuthUserError):
        get_user_role_ids(0, fetch_all=FakeFetchAll({}))


def test_get_user_role_ids_invalid_row_is_explicit():
    fetch = FakeFetchAll({SELECT_USER_ROLE_IDS_SQL: [{"id": 1}]})

    with pytest.raises(AuthUserRbacResolverError):
        get_user_role_ids(42, fetch_all=fetch)


def test_get_user_permissions_resolves_permissions_for_user():
    fetch = FakeFetchAll({
        SELECT_USER_PERMISSIONS_SQL: [
            {"code": "articles.view"},
            {"code": "Articles.Edit"},
        ],
    })

    assert get_user_permissions(42, fetch_all=fetch) == (
        "articles.edit",
        "articles.view",
    )
    assert fetch.calls == [(SELECT_USER_PERMISSIONS_SQL, (42,))]


def test_get_user_permissions_removes_duplicates_from_multiple_roles():
    fetch = FakeFetchAll({
        SELECT_USER_PERMISSIONS_SQL: [
            {"code": "articles.view"},
            {"code": "articles.view"},
            {"code": "Articles.View"},
            {"code": "articles.edit"},
        ],
    })

    assert get_user_permissions(42, fetch_all=fetch) == (
        "articles.edit",
        "articles.view",
    )


def test_get_user_permissions_user_without_role_returns_empty_tuple():
    fetch = FakeFetchAll({SELECT_USER_PERMISSIONS_SQL: []})

    assert get_user_permissions(42, fetch_all=fetch) == ()


def test_get_user_permissions_role_without_permission_returns_empty_tuple():
    fetch = FakeFetchAll({SELECT_USER_PERMISSIONS_SQL: []})

    assert get_user_permissions(42, fetch_all=fetch) == ()


def test_get_user_permissions_role_deleted_or_unknown_returns_empty_tuple():
    fetch = FakeFetchAll({SELECT_USER_PERMISSIONS_SQL: []})

    assert get_user_permissions(42, fetch_all=fetch) == ()


def test_get_user_permissions_invalid_user_id_raises():
    with pytest.raises(InvalidAuthUserError):
        get_user_permissions(-1, fetch_all=FakeFetchAll({}))


def test_get_user_permissions_invalid_row_is_explicit():
    fetch = FakeFetchAll({SELECT_USER_PERMISSIONS_SQL: [{"permission": "x"}]})

    with pytest.raises(AuthUserRbacResolverError):
        get_user_permissions(42, fetch_all=fetch)


def test_user_has_permission_true_when_present():
    fetch = FakeFetchAll({
        SELECT_USER_PERMISSIONS_SQL: [{"code": "articles.view"}],
    })

    assert user_has_permission(42, "articles.view", fetch_all=fetch) is True


def test_user_has_permission_normalizes_requested_permission():
    fetch = FakeFetchAll({
        SELECT_USER_PERMISSIONS_SQL: [{"code": "articles.view"}],
    })

    assert user_has_permission(42, "Articles View", fetch_all=fetch) is True


def test_user_has_permission_false_when_absent():
    fetch = FakeFetchAll({
        SELECT_USER_PERMISSIONS_SQL: [{"code": "articles.view"}],
    })

    assert user_has_permission(42, "articles.delete", fetch_all=fetch) is False


def test_user_has_permission_false_for_unknown_permission():
    fetch = FakeFetchAll({
        SELECT_USER_PERMISSIONS_SQL: [{"code": "articles.view"}],
    })

    assert user_has_permission(42, "users.delete", fetch_all=fetch) is False


def test_user_has_permission_false_for_invalid_user_id():
    assert user_has_permission(0, "articles.view", fetch_all=FakeFetchAll({})) is False


def test_user_has_permission_false_for_empty_permission():
    assert user_has_permission(42, " ", fetch_all=FakeFetchAll({})) is False


def test_missing_user_roles_or_rbac_tables_grants_no_permission():
    def missing_table(_sql: str, _params: tuple):
        raise RuntimeError("Table 'user_roles' doesn't exist")

    assert get_user_role_ids(42, fetch_all=missing_table) == ()
    assert get_user_permissions(42, fetch_all=missing_table) == ()
    assert user_has_permission(42, "articles.view", fetch_all=missing_table) is False


def test_unexpected_database_error_is_explicit():
    def broken(_sql: str, _params: tuple):
        raise RuntimeError("connection refused")

    with pytest.raises(AuthUserRbacResolverError):
        get_user_permissions(42, fetch_all=broken)


def test_permission_sql_uses_user_roles_roles_and_permissions():
    assert "FROM user_roles ur" in SELECT_USER_PERMISSIONS_SQL
    assert "JOIN roles r ON r.id = ur.role_id" in SELECT_USER_PERMISSIONS_SQL
    assert "JOIN role_permissions rp ON rp.role_id = r.id" in SELECT_USER_PERMISSIONS_SQL
    assert "JOIN permissions p ON p.id = rp.permission_id" in SELECT_USER_PERMISSIONS_SQL
    assert "SELECT DISTINCT p.code AS code" in SELECT_USER_PERMISSIONS_SQL


def test_role_sql_reads_only_user_roles():
    assert "FROM user_roles" in SELECT_USER_ROLE_IDS_SQL
    assert "WHERE user_id = ?" in SELECT_USER_ROLE_IDS_SQL


def test_auth_user_model_does_not_store_permissions():
    user = AuthUser(id=1, email="a@example.test", password_hash="hash")

    assert not hasattr(user, "permissions")
    assert not hasattr(user, "roles")
    assert not hasattr(user, "can")


def test_resolver_keeps_auth_and_rbac_separated():
    import forge_mvc_rbac.resolver as module

    source = inspect.getsource(module)
    assert "require_permission" not in source
    assert "make_can" not in source
    assert "current_user" not in source
    assert "INSERT INTO" not in source
    assert "UPDATE " not in source


def test_resolver_has_no_external_dependency():
    import forge_mvc_rbac.resolver as module

    source = inspect.getsource(module)
    for forbidden in ("requests", "urllib", "httpx", "sqlalchemy", "django"):
        assert forbidden not in source


def test_resolver_has_no_jinja_logic():
    import forge_mvc_rbac.resolver as module

    source = inspect.getsource(module).lower()
    assert "jinja" not in source
    assert "template" not in source


def test_missing_table_detected_by_errno_even_with_localized_message():
    """SEC-RBAC-MISSING-TABLE-DETECT-001 : détection par code d'erreur driver.

    Une erreur « table absente » dont le message est localisé (donc ne contient
    aucun marqueur anglais) mais qui porte `errno == 1146` (ER_NO_SUCH_TABLE)
    doit quand même être reconnue, contrairement au seul string-matching.
    """
    class _LocalizedDbError(Exception):
        def __init__(self):
            super().__init__("La table « user_roles » est introuvable")
            self.errno = 1146

    def missing_table_errno(_sql: str, _params: tuple):
        raise _LocalizedDbError()

    assert get_user_role_ids(42, fetch_all=missing_table_errno) == ()
    assert get_user_permissions(42, fetch_all=missing_table_errno) == ()
    assert user_has_permission(42, "articles.view", fetch_all=missing_table_errno) is False
