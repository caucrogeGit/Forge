"""Forge RBAC — rôles, permissions, autorisations et helpers Jinja."""

from __future__ import annotations

from forge_mvc_rbac.authorization import auth_user_can, require_user_permission
from forge_mvc_rbac.jinja import (
    AuthJinjaUser,
    get_jinja_current_user,
    make_auth_jinja_can,
    make_auth_jinja_context,
    make_auth_jinja_context_with_can,
    sanitize_jinja_user,
)
from forge_mvc_rbac.rbac import (
    Permission,
    PermissionDenied,
    RbacValidationError,
    Role,
    get_request_permissions,
    has_permission,
    make_can,
    normalize_permission_code,
    normalize_role_slug,
    require_permission,
    validate_permission,
    validate_role,
)
from forge_mvc_rbac.resolver import (
    AuthUserRbacResolverError,
    FetchAll,
    get_user_permissions,
    get_user_role_ids,
    user_has_permission,
)
from forge_mvc_rbac.user_rbac import (
    AuthUserRole,
    auth_user_role_key,
    auth_user_roles_match,
    create_auth_user_role,
    is_valid_auth_user_role,
    normalize_auth_user_role,
    user_role_key,
    validate_auth_user_role_contract,
    validate_user_role_role_id,
    validate_user_role_user_id,
)

__version__ = "1.0.0b2"

# Auto-enregistrement dans le registre de contexte Jinja de core.
try:
    from core.mvc.controller.registry import register_jinja_context_provider
    from forge_mvc_rbac.jinja import make_auth_jinja_context_with_can
    register_jinja_context_provider(make_auth_jinja_context_with_can)
except ImportError:
    pass

__all__ = [
    "auth_user_can",
    "require_user_permission",
    "AuthJinjaUser",
    "get_jinja_current_user",
    "make_auth_jinja_can",
    "make_auth_jinja_context",
    "make_auth_jinja_context_with_can",
    "sanitize_jinja_user",
    "Permission",
    "PermissionDenied",
    "RbacValidationError",
    "Role",
    "get_request_permissions",
    "has_permission",
    "make_can",
    "normalize_permission_code",
    "normalize_role_slug",
    "require_permission",
    "validate_permission",
    "validate_role",
    "AuthUserRbacResolverError",
    "FetchAll",
    "get_user_permissions",
    "get_user_role_ids",
    "user_has_permission",
    "AuthUserRole",
    "auth_user_role_key",
    "auth_user_roles_match",
    "create_auth_user_role",
    "is_valid_auth_user_role",
    "normalize_auth_user_role",
    "user_role_key",
    "validate_auth_user_role_contract",
    "validate_user_role_role_id",
    "validate_user_role_user_id",
]
