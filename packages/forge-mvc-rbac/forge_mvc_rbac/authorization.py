"""Protection serveur Auth/User branchee sur les permissions RBAC."""

from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from typing import Any

from core.auth.session import get_authenticated_user_id
from forge_mvc_rbac.resolver import FetchAll, user_has_permission
from core.http.response import Response
from forge_mvc_rbac.rbac import normalize_permission_code, validate_permission


PermissionChecker = Callable[..., bool]


def auth_user_can(
    request: Any,
    permission: str,
    *,
    fetch_all: FetchAll | None = None,
    permission_checker: PermissionChecker | None = None,
) -> bool:
    """Retourne True si l'utilisateur Auth/User connecte possede permission."""
    user_id = get_authenticated_user_id(request)
    if user_id is None:
        return False

    normalized = normalize_permission_code(permission)
    if not normalized:
        return False

    checker = permission_checker or user_has_permission
    try:
        return bool(checker(user_id, normalized, fetch_all=fetch_all))
    except Exception:
        return False


def require_user_permission(
    permission: str,
    *,
    fetch_all: FetchAll | None = None,
    permission_checker: PermissionChecker | None = None,
):
    """Protege une route avec les permissions RBAC de l'utilisateur Auth/User."""
    normalized = normalize_permission_code(permission)
    validate_permission(normalized)

    def decorator(func):
        @wraps(func)
        def wrapper(request: Any, *args: Any, **kwargs: Any):
            user_id = get_authenticated_user_id(request)
            if user_id is None:
                return Response(
                    401,
                    body=b"Authentication required",
                    content_type="text/plain; charset=utf-8",
                )

            checker = permission_checker or user_has_permission
            try:
                allowed = bool(checker(user_id, normalized, fetch_all=fetch_all))
            except Exception:
                allowed = False

            if not allowed:
                return Response(
                    403,
                    body=f"Permission required: {normalized}".encode(),
                    content_type="text/plain; charset=utf-8",
                )

            return func(request, *args, **kwargs)

        return wrapper

    return decorator
