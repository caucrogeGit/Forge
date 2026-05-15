"""Contexte Jinja Auth/User et RBAC.

Cette couche expose des informations d'affichage aux templates. Elle ne
remplace pas les protections serveur par decorateurs ou controleurs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from core.auth.session import (
    current_user as load_current_user,
    get_authenticated_user_id,
)
from core.auth.user import AuthUser
from forge_mvc_rbac.rbac import make_can
from forge_mvc_rbac.resolver import FetchAll, user_has_permission


@dataclass(frozen=True)
class AuthJinjaUser:
    """Utilisateur expose aux templates, sans secret ni hash de mot de passe."""

    id: int
    email: str | None = None
    is_active: bool | None = None


def sanitize_jinja_user(user: Any) -> AuthJinjaUser | None:
    """Retourne une representation publique minimale d'un utilisateur."""
    if isinstance(user, AuthJinjaUser):
        return user

    if isinstance(user, AuthUser):
        return AuthJinjaUser(id=user.id, email=user.email, is_active=user.is_active)

    if isinstance(user, dict):
        user_id = user.get("id")
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            return None

        email = user.get("email")
        if email is not None and not isinstance(email, str):
            email = None

        is_active = user.get("is_active")
        if is_active is not None and not isinstance(is_active, bool):
            is_active = None

        return AuthJinjaUser(id=user_id, email=email, is_active=is_active)

    return None


def get_jinja_current_user(
    request: Any,
    *,
    user_loader: Callable[[int], Any] | None = None,
) -> AuthJinjaUser | None:
    """Retourne l'utilisateur public courant pour Jinja, ou None."""
    if user_loader is not None:
        return sanitize_jinja_user(load_current_user(request, user_loader))

    user_id = get_authenticated_user_id(request)
    if user_id is None:
        return None
    return AuthJinjaUser(id=user_id)


def make_auth_jinja_can(
    request: Any,
    *,
    fetch_all: FetchAll | None = None,
    permission_checker: Callable[..., bool] | None = None,
    fallback_can: Callable[[str], bool] | None = None,
) -> Callable[[str], bool]:
    """Construit le helper can(permission) expose aux templates."""
    checker = permission_checker or user_has_permission

    def can(permission: str) -> bool:
        user_id = get_authenticated_user_id(request)
        if user_id is None:
            if fallback_can is None:
                return False
            try:
                return bool(fallback_can(permission))
            except Exception:
                return False

        try:
            return bool(checker(user_id, permission, fetch_all=fetch_all))
        except Exception:
            return False

    return can


def make_auth_jinja_context(
    request: Any,
    *,
    user_loader: Callable[[int], Any] | None = None,
    fetch_all: FetchAll | None = None,
    permission_checker: Callable[..., bool] | None = None,
    fallback_can: Callable[[str], bool] | None = None,
) -> dict[str, Any]:
    """Retourne le contexte Auth/User standard pour les templates Jinja."""
    current_user = get_jinja_current_user(request, user_loader=user_loader)
    return {
        "current_user": current_user,
        "is_authenticated": current_user is not None,
        "can": make_auth_jinja_can(
            request,
            fetch_all=fetch_all,
            permission_checker=permission_checker,
            fallback_can=fallback_can,
        ),
    }


def make_auth_jinja_context_with_can(request: Any) -> dict[str, Any]:
    """Wrapper sans argument pour le registre core — délègue à make_auth_jinja_context."""
    return make_auth_jinja_context(request, fallback_can=make_can(request))
