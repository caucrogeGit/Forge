# pyright: strict
"""
forge_mvc_rbac/rbac.py — Modèles génériques Role et Permission, autorisation

Socle de données RBAC sans ORM.
- Role       : rôle portant un slug unique.
- Permission : capacité atomique identifiée par un code pointé (ex. "posts.edit").
- require_permission : primitive bas niveau lisant request.permissions
  (voir le docstring du paquet pour le choix de la garde de route officielle).
"""

from __future__ import annotations

import functools
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any


# ---------------------------------------------------------------------------
# Modèles
# ---------------------------------------------------------------------------


@dataclass
class Role:
    id: int | None
    name: str
    slug: str
    description: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Role":
        return cls(
            id=row.get("id"),
            name=row["name"],
            slug=row["slug"],
            description=row.get("description"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
        }


@dataclass
class Permission:
    id: int | None
    code: str
    label: str | None = None
    description: str | None = None

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> "Permission":
        return cls(
            id=row.get("id"),
            code=row["code"],
            label=row.get("label"),
            description=row.get("description"),
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "label": self.label,
            "description": self.description,
        }


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------

_SLUG_INVALID = re.compile(r"[^a-z0-9\-]")
_CODE_INVALID = re.compile(r"[^a-z0-9\._\-]")
_MULTI_SEP = re.compile(r"[-]{2,}")


def normalize_role_slug(name: str) -> str:
    """
    Dérive un slug valide depuis un nom de rôle.

    "Super Admin" → "super-admin"
    """
    slug = name.strip().lower()
    slug = slug.replace(" ", "-").replace("_", "-")
    slug = _SLUG_INVALID.sub("", slug)
    slug = _MULTI_SEP.sub("-", slug)
    return slug.strip("-")


def normalize_permission_code(code: str) -> str:
    """
    Normalise un code de permission en minuscules avec séparateurs pointés.

    "Posts.Edit" → "posts.edit"
    "POSTS EDIT" → "posts.edit"
    """
    normalized = code.strip().lower()
    normalized = normalized.replace(" ", ".").replace("-", ".").replace("_", ".")
    normalized = _CODE_INVALID.sub("", normalized)
    # Éliminer les points multiples consécutifs
    while ".." in normalized:
        normalized = normalized.replace("..", ".")
    return normalized.strip(".")


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------


class RbacValidationError(ValueError):
    """Erreur de validation RBAC."""


def validate_role(name: str, slug: str) -> None:
    """
    Lève RbacValidationError si le rôle est invalide.
    Valide : name non vide, slug non vide et sans espaces.
    """
    if not name or not name.strip():
        raise RbacValidationError("Le nom du rôle ne peut pas être vide.")
    if not slug or not slug.strip():
        raise RbacValidationError("Le slug du rôle ne peut pas être vide.")
    if " " in slug:
        raise RbacValidationError(f"Le slug '{slug}' ne doit pas contenir d'espace.")


def validate_permission(code: str) -> None:
    """
    Lève RbacValidationError si le code de permission est invalide.
    Valide : non vide, notation pointée, pas d'espace.
    """
    if not code or not code.strip():
        raise RbacValidationError("Le code de permission ne peut pas être vide.")
    if " " in code:
        raise RbacValidationError(f"Le code '{code}' ne doit pas contenir d'espace.")
    if "." not in code:
        raise RbacValidationError(
            f"Le code '{code}' doit utiliser la notation pointée (ex. 'posts.edit')."
        )


# ---------------------------------------------------------------------------
# Autorisation
# ---------------------------------------------------------------------------

from core.http.response import Response          # noqa: E402
from core.security.session import get_user  # noqa: E402


class PermissionDenied(Exception):
    """Levée quand une permission requise est absente."""


def get_request_permissions(request: Any) -> set[str]:
    """
    Résout les permissions de la requête courante.

    Ordre de résolution :
    1. request.permissions (injection directe, tests)
    2. session utilisateur → champ "permissions"
    3. ensemble vide
    """
    injected = getattr(request, "permissions", None)
    if injected is not None:
        return set(injected)
    utilisateur = get_user(request)
    if utilisateur:
        return set(utilisateur.get("permissions", []))
    return set()


def has_permission(request: Any, permission_code: str) -> bool:
    """Retourne True si la requête possède la permission donnée."""
    return permission_code in get_request_permissions(request)


def require_permission(permission_code: str):
    """
    Décorateur : retourne 403 si la permission est absente.

    Valide le code à la décoration. Normalise avant la vérification.

    Usage :
        @staticmethod
        @require_auth
        @require_permission("posts.edit")
        def edit(request): ...
    """
    validate_permission(permission_code)
    normalized = normalize_permission_code(permission_code)

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            if not has_permission(request, normalized):
                return Response(403, body=f"Permission required: {normalized}".encode())
            return func(request, *args, **kwargs)
        return wrapper
    return decorator


def make_can(request: Any) -> Callable[[str], bool]:
    """
    Retourne un callable can(code) -> bool lié à la request courante.

    Injecter dans le contexte Jinja2 pour usage dans les templates :
        ctx["can"] = make_can(request)

    Retourne False pour tout code invalide ou absent — ne propage jamais
    d'exception vers le template.
    """
    def can(permission_code: str) -> bool:
        try:
            normalized = normalize_permission_code(permission_code)
            return has_permission(request, normalized)
        except Exception:
            return False
    return can
