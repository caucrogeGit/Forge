# pyright: strict
"""Contexte Jinja Auth/User et RBAC.

Cette couche expose des informations d'affichage aux templates. Elle ne
remplace pas les protections serveur par decorateurs ou controleurs.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

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
        user_dict = cast("dict[str, Any]", user)
        user_id = user_dict.get("id")
        if not isinstance(user_id, int) or isinstance(user_id, bool) or user_id <= 0:
            return None

        email = user_dict.get("email")
        if email is not None and not isinstance(email, str):
            email = None

        is_active = user_dict.get("is_active")
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


# ── Modèle CONTRAT (rbac.json) : provider Jinja natif (manque terrain C) ────────

def make_contract_jinja_can(
    request: Any, *, project_root: "str | Path" = ".",
) -> Callable[[str], bool]:
    """``can(permission)`` adossé au **contrat** (rbac.json), pour le modèle contrat.

    Réutilise ``get_request_roles`` (request.roles puis résolution en base sous
    l'auth moderne, puis session legacy) et ``has_contract_permission``. Ne requiert
    **aucune** table du modèle table (à la différence du provider par défaut). Ne
    lève jamais vers le template.
    """
    from forge_mvc_rbac.contract import (
        get_request_roles,
        has_contract_permission,
        load_rbac_contract,
    )

    def can(permission: str) -> bool:
        try:
            result = load_rbac_contract(project_root)
            roles = get_request_roles(request)
            return has_contract_permission(result, roles, permission)
        except Exception:
            return False

    return can


def make_contract_jinja_context(
    request: Any, *, project_root: "str | Path" = ".",
) -> dict[str, Any]:
    """Contexte Jinja du modèle contrat : ``current_user`` + ``is_authenticated`` + ``can()`` contractuel."""
    current = get_jinja_current_user(request)
    return {
        "current_user": current,
        "is_authenticated": current is not None,
        "can": make_contract_jinja_can(request, project_root=project_root),
    }


def make_contract_jinja_context_with_can(request: Any) -> dict[str, Any]:
    """Wrapper sans argument pour le registre core (projet = répertoire courant)."""
    return make_contract_jinja_context(request)


def register_contract_rbac_provider() -> None:
    """Enregistre le provider Jinja du **modèle contrat** dans le registre core.

    À appeler par une application en modèle contrat (rbac.json), au lieu du provider
    table auto-enregistré : le ``can()`` des templates s'adosse alors au contrat,
    sans les tables du modèle table. Remplace un provider maison.
    """
    from core.mvc.controller.registry import register_jinja_context_provider

    register_jinja_context_provider(make_contract_jinja_context_with_can)
