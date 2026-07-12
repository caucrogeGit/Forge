# pyright: strict
"""Resolution backend des permissions RBAC d'un utilisateur Auth/User.

Ce module fait le pont de lecture user_id -> user_roles -> roles -> permissions.
Il ne definit pas les permissions et ne modifie pas le moteur RBAC.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import Any

from core.auth.exceptions import AuthError
from forge_mvc_rbac.user_rbac import validate_user_role_user_id
from forge_mvc_rbac.rbac import normalize_permission_code


FetchAll = Callable[[str, tuple[Any, ...]], Iterable[dict[str, Any]]]


class AuthUserRbacResolverError(AuthError):
    """Erreur explicite de resolution Auth/User vers RBAC."""


SELECT_USER_ROLE_IDS_SQL = """\
SELECT role_id
FROM user_roles
WHERE user_id = ?
ORDER BY role_id
"""


SELECT_USER_ROLE_SLUGS_SQL = """\
SELECT r.slug AS slug
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id
WHERE ur.user_id = ?
ORDER BY r.slug
"""


SELECT_USER_PERMISSIONS_SQL = """\
SELECT DISTINCT p.code AS code
FROM user_roles ur
JOIN roles r ON r.id = ur.role_id
JOIN role_permissions rp ON rp.role_id = r.id
JOIN permissions p ON p.id = rp.permission_id
WHERE ur.user_id = ?
ORDER BY p.code
"""


_MISSING_TABLE_ERRNO = 1146  # MySQL/MariaDB ER_NO_SUCH_TABLE

_MISSING_TABLE_MARKERS = (
    "doesn't exist",
    "no such table",
    "unknown table",
    "undefined table",
)


def _default_fetch_all(sql: str, params: tuple[Any, ...]) -> Iterable[dict[str, Any]]:
    from core.database import db

    return db.fetch_all(sql, params)


def _is_missing_table_error(error: Exception) -> bool:
    # Détection canonique par code d'erreur du driver (robuste à la locale et à
    # la version du serveur) : MariaDB/MySQL exposent `errno` sur leurs exceptions.
    if getattr(error, "errno", None) == _MISSING_TABLE_ERRNO:
        return True
    # Repli string-matching pour les drivers sans `errno` ou les erreurs enveloppées.
    message = str(error).lower()
    return any(marker in message for marker in _MISSING_TABLE_MARKERS)


def _fetch_rows(
    fetch_all: FetchAll | None,
    sql: str,
    params: tuple[Any, ...],
) -> Iterable[dict[str, Any]]:
    reader = fetch_all or _default_fetch_all
    try:
        rows = reader(sql, params)
    except Exception as error:
        if _is_missing_table_error(error):
            return ()
        raise AuthUserRbacResolverError(
            f"resolution RBAC utilisateur impossible : {error}"
        ) from error
    return rows or ()


def get_user_role_ids(
    user_id: int,
    *,
    fetch_all: FetchAll | None = None,
) -> tuple[int, ...]:
    """Retourne les role_id associes a user_id, sans doublons."""
    validate_user_role_user_id(user_id)

    role_ids: set[int] = set()
    for row in _fetch_rows(fetch_all, SELECT_USER_ROLE_IDS_SQL, (user_id,)):
        if not isinstance(row, dict) or "role_id" not in row:  # pyright: ignore[reportUnnecessaryIsInstance]
            raise AuthUserRbacResolverError("ligne user_roles invalide")

        role_id = row["role_id"]
        if isinstance(role_id, bool) or not isinstance(role_id, int) or role_id <= 0:
            raise AuthUserRbacResolverError("role_id user_roles invalide")
        role_ids.add(role_id)

    return tuple(sorted(role_ids))


def get_user_role_slugs(
    user_id: int,
    *,
    fetch_all: FetchAll | None = None,
) -> tuple[str, ...]:
    """Retourne les slugs de rôles associés à user_id (pont vers le contrat RBAC).

    Fait le lien user_id -> user_roles -> roles.slug. Les slugs sont l'identité
    des rôles côté contrat (rbac.json), d'où ce résolveur dédié en plus des
    role_id. Retourne un tuple sans doublon, dans l'ordre des slugs ; tuple vide
    si aucune table (mode dégradé) ou aucun rôle.
    """
    validate_user_role_user_id(user_id)

    slugs: list[str] = []
    seen: set[str] = set()
    for row in _fetch_rows(fetch_all, SELECT_USER_ROLE_SLUGS_SQL, (user_id,)):
        if not isinstance(row, dict) or "slug" not in row:  # pyright: ignore[reportUnnecessaryIsInstance]
            raise AuthUserRbacResolverError("ligne roles invalide")
        slug = row["slug"]
        if not isinstance(slug, str) or not slug:
            raise AuthUserRbacResolverError("slug de rôle invalide")
        if slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return tuple(slugs)


def get_user_permissions(
    user_id: int,
    *,
    fetch_all: FetchAll | None = None,
) -> tuple[str, ...]:
    """Retourne les permissions RBAC effectives de user_id, sans doublons."""
    validate_user_role_user_id(user_id)

    permissions: set[str] = set()
    for row in _fetch_rows(fetch_all, SELECT_USER_PERMISSIONS_SQL, (user_id,)):
        if not isinstance(row, dict) or "code" not in row:  # pyright: ignore[reportUnnecessaryIsInstance]
            raise AuthUserRbacResolverError("ligne permission RBAC invalide")

        code = row["code"]
        if not isinstance(code, str) or not code.strip():
            raise AuthUserRbacResolverError("code permission RBAC invalide")

        normalized = normalize_permission_code(code)
        if normalized:
            permissions.add(normalized)

    return tuple(sorted(permissions))


def user_has_permission(
    user_id: int,
    permission: str,
    *,
    fetch_all: FetchAll | None = None,
) -> bool:
    """Retourne True si user_id possede permission. Par defaut, aucun acces."""
    try:
        validate_user_role_user_id(user_id)
        if not isinstance(permission, str) or not permission.strip():  # pyright: ignore[reportUnnecessaryIsInstance]
            return False

        normalized = normalize_permission_code(permission)
        if not normalized:
            return False

        return normalized in get_user_permissions(user_id, fetch_all=fetch_all)
    except AuthUserRbacResolverError:
        raise
    except Exception:
        return False
