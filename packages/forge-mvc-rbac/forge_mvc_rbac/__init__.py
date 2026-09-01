# pyright: strict
"""Forge RBAC — rôles, permissions, autorisations et helpers Jinja.

Protéger une route par permission : il existe trois niveaux, à choisir selon la
source des permissions (ce n'est pas trois façons de faire la même chose, mais
trois contextes distincts) :

- ``require_contract_permission`` (recommandé, déclaratif) : garde de route
  basée sur le contrat RBAC chargé, sans base de données. C'est la voie promue
  par le parcours welcome-rbac et la façon officielle par défaut.
- ``require_user_permission`` / ``auth_user_can`` : résolution des permissions
  de l'utilisateur Auth/User **connecté** depuis la base (via
  ``user_has_permission``). À utiliser quand les permissions vivent en base.
- ``require_permission`` / ``has_permission`` : primitive bas niveau qui lit des
  permissions déjà chargées dans ``request.permissions`` (à peupler en amont).

Toutes échouent fermé (401/403). En cas de doute, utiliser
``require_contract_permission``.

``has_instance_permission`` n'est pas un quatrième niveau : elle **compose**
au dessus de celui que l'appelant choisit, pour répondre à « peut il agir sur
CET objet » (RBAC-INSTANCE-PERMISSIONS-001).
"""

from __future__ import annotations

from forge_mvc_rbac.contract import (
    RbacContractError,
    RbacContractResult,
    contract_permission_required,
    get_contract_permissions,
    get_request_roles,
    has_contract_permission,
    load_rbac_contract,
    require_contract_permission,
    require_contract_permission_for_request,
)
from forge_mvc_rbac.authorization import auth_user_can, require_user_permission
from forge_mvc_rbac.instance import (
    InstancePermissionDenied,
    OwnershipCheck,
    PermissionCheck,
    has_instance_permission,
    require_instance_permission,
)
from forge_mvc_rbac.prefix_guard import PrefixPermissionMiddleware
from forge_mvc_rbac.jinja import (
    AuthJinjaUser,
    get_jinja_current_user,
    make_auth_jinja_can,
    make_auth_jinja_context,
    make_auth_jinja_context_with_can,
    make_contract_jinja_can,
    make_contract_jinja_context,
    make_contract_jinja_context_with_can,
    register_contract_rbac_provider,
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

__version__ = "1.0.0rc7"

# Auto-enregistrement dans le registre de contexte Jinja de core.
try:
    from core.mvc.controller.registry import register_jinja_context_provider
    from forge_mvc_rbac.jinja import make_auth_jinja_context_with_can
    register_jinja_context_provider(make_auth_jinja_context_with_can)
except ImportError:
    pass

__all__ = [
    "load_rbac_contract",
    "RbacContractResult",
    "RbacContractError",
    "get_contract_permissions",
    "get_request_roles",
    "has_contract_permission",
    "require_contract_permission",
    "require_contract_permission_for_request",
    # Permission portant sur une instance (RBAC-INSTANCE-PERMISSIONS-001)
    "has_instance_permission",
    "require_instance_permission",
    "InstancePermissionDenied",
    "OwnershipCheck",
    "PermissionCheck",
    "contract_permission_required",
    "auth_user_can",
    "require_user_permission",
    "AuthJinjaUser",
    "get_jinja_current_user",
    "make_auth_jinja_can",
    "make_auth_jinja_context",
    "make_auth_jinja_context_with_can",
    "make_contract_jinja_can",
    "make_contract_jinja_context",
    "make_contract_jinja_context_with_can",
    "register_contract_rbac_provider",
    "PrefixPermissionMiddleware",
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
