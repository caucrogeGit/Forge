# pyright: strict
"""Chargeur du contrat RBAC depuis mvc/security/rbac.json.

Ce module charge et valide le contrat déclaratif RBAC d'un projet Forge.
Il ne branche pas les routes, ne modifie pas make:crud, ne crée aucun fichier.

Comportement :
  - fichier absent  → valid=True, exists=False  (RBAC est opt-in)
  - fichier valide  → valid=True, exists=True, data fourni
  - fichier invalide → valid=False, exists=True, errors fournis
  - jsonschema absent → dégradation douce, valid=True sans validation de schéma
"""

from __future__ import annotations

import functools
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

from core.http.response import Response          # noqa: E402
from core.sessions.keys import (                 # noqa: E402
    SESSION_KEY_AUTHENTICATED,
    SESSION_KEY_USER,
    session_get,
)


_RBAC_CONTRACT_RELATIVE = Path("mvc") / "security" / "rbac.json"
_RBAC_SCHEMA_ID = "https://forge-mvc.dev/schemas/rbac.schema.json"


# ---------------------------------------------------------------------------
# Structures de résultat
# ---------------------------------------------------------------------------


@dataclass
class RbacContractError:
    """Erreur de validation du contrat RBAC."""

    path: str
    message: str


@dataclass
class RbacContractResult:
    """Résultat du chargement et de la validation du contrat RBAC."""

    valid: bool
    exists: bool
    path: str
    roles_count: int = 0
    entities_count: int = 0
    errors: list[RbacContractError] = field(default_factory=list[RbacContractError])
    data: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def _find_schemas_dir() -> Path | None:
    # Le schéma RBAC est embarqué par cet opt-in (ADR-056), plus dans le cœur.
    candidate = Path(__file__).resolve().parent / "schemas"
    if candidate.is_dir():
        return candidate
    return None


def _build_registry(schemas_dir: Path) -> Any:
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        return None

    resources: list[Any] = []
    for f in schemas_dir.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            sid = schema.get("$id")
            if sid:
                resources.append(
                    (sid, Resource.from_contents(schema, default_specification=DRAFT202012))
                )
        except Exception:
            pass

    try:
        # referencing.Registry est générique ; ses paramètres de type ne sont
        # pas résolus par pyright (dépendance optionnelle). Le retour est Any.
        return Registry().with_resources(resources)  # pyright: ignore[reportUnknownMemberType, reportUnknownVariableType, reportUnknownArgumentType]
    except Exception:
        return None


def _make_validator(schemas_dir: Path, registry: Any) -> Any:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None

    for f in schemas_dir.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            if schema.get("$id") == _RBAC_SCHEMA_ID:
                return Draft202012Validator(schema, registry=registry)
        except Exception:
            pass
    return None


def _collect_errors(validator: Any, instance: dict[str, Any]) -> list[RbacContractError]:
    errors: list[RbacContractError] = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: str(e.absolute_path)):
        path = "$." + ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "$"
        errors.append(RbacContractError(path=path, message=error.message))
    return errors


def _count_roles(instance: dict[str, Any]) -> int:
    roles = instance.get("roles")
    return len(cast("dict[Any, Any]", roles)) if isinstance(roles, dict) else 0


def _count_entities(instance: dict[str, Any]) -> int:
    entities = instance.get("entities")
    return len(cast("dict[Any, Any]", entities)) if isinstance(entities, dict) else 0


def _result_degraded(path_str: str, instance: dict[str, Any]) -> RbacContractResult:
    return RbacContractResult(
        valid=True,
        exists=True,
        path=path_str,
        roles_count=_count_roles(instance),
        entities_count=_count_entities(instance),
        data=instance,
    )


# ---------------------------------------------------------------------------
# API publique
# ---------------------------------------------------------------------------


def load_rbac_contract(project_root: str | Path = ".") -> RbacContractResult:
    """Charge et valide mvc/security/rbac.json depuis project_root.

    Lecture seule : aucun fichier n'est créé ni modifié.
    """
    root = Path(project_root).resolve()
    rbac_path = root / _RBAC_CONTRACT_RELATIVE
    path_str = str(_RBAC_CONTRACT_RELATIVE)

    if not rbac_path.exists():
        return RbacContractResult(valid=True, exists=False, path=path_str)

    try:
        instance = json.loads(rbac_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return RbacContractResult(
            valid=False,
            exists=True,
            path=path_str,
            errors=[RbacContractError(path="$", message=f"Fichier JSON invalide : {exc}")],
        )

    schemas_dir = _find_schemas_dir()
    if schemas_dir is None:
        return _result_degraded(path_str, instance)

    registry = _build_registry(schemas_dir)
    if registry is None:
        return _result_degraded(path_str, instance)

    validator = _make_validator(schemas_dir, registry)
    if validator is None:
        return _result_degraded(path_str, instance)

    errors = _collect_errors(validator, instance)
    is_valid = not errors

    return RbacContractResult(
        valid=is_valid,
        exists=True,
        path=path_str,
        roles_count=_count_roles(instance),
        entities_count=_count_entities(instance),
        errors=errors,
        data=instance if is_valid else None,
    )


def get_contract_permissions(result: RbacContractResult, roles: Iterable[str]) -> set[str]:
    """Retourne l'ensemble des permissions accordées aux rôles selon le contrat.

    Retourne un ensemble vide si le contrat est absent, invalide ou si aucun
    des rôles fournis n'est déclaré dans le contrat.
    """
    if not result.valid or not result.exists or result.data is None:
        return set()

    contract_roles = result.data.get("roles", {})
    if not isinstance(contract_roles, dict):
        return set()

    permissions: set[str] = set()
    for role in roles:
        role_perms = cast("dict[str, Any]", contract_roles).get(role)
        if isinstance(role_perms, list):
            for perm in cast("list[Any]", role_perms):
                if isinstance(perm, str) and perm.strip():
                    permissions.add(perm)
    return permissions


def has_contract_permission(
    result: RbacContractResult,
    roles: Iterable[str],
    permission: str,
) -> bool:
    """Retourne True si au moins un des rôles possède la permission selon le contrat.

    Retourne False si le contrat est absent, invalide, si le rôle est inconnu
    ou si la permission n'est pas déclarée pour ce rôle.
    """
    if not result.valid or not result.exists:
        return False
    return permission in get_contract_permissions(result, roles)


def require_contract_permission(
    result: RbacContractResult,
    roles: Iterable[str],
    permission: str,
) -> Response | None:
    """Vérifie une permission contractuelle.

    Retourne None si la permission est accordée.
    Retourne Response(403) si la permission est refusée ou si le contrat est absent.

    Usage dans un contrôleur :
        response = require_contract_permission(contract, user_roles, "article.list")
        if response is not None:
            return response
    """
    if has_contract_permission(result, roles, permission):
        return None
    return Response(403, body=f"Permission required: {permission}".encode())


# ---------------------------------------------------------------------------
# Guards opt-in pour routes et contrôleurs
# ---------------------------------------------------------------------------


def _legacy_session_user(request: Any) -> "dict[str, Any] | None":
    """Utilisateur de la session **legacy** (dépréciée), sans passer par le
    `core.security.session.get_user` déprécié : on résout la session via les
    primitives non dépréciées et on lit directement les clés legacy.

    Retourne None si la session est absente ou non authentifiée.
    """
    from core.security.session import get_session, get_session_id

    session_id = get_session_id(request)
    if not session_id:
        return None
    session = get_session(session_id)
    if not session or not session_get(session, SESSION_KEY_AUTHENTICATED):
        return None
    user = session_get(session, SESSION_KEY_USER)
    return cast("dict[str, Any]", user) if isinstance(user, dict) else None


def get_request_roles(request: Any) -> list[str]:
    """Extrait les rôles de la requête/session courante.

    Ordre de résolution :
    1. `request.roles` — **point d'injection canonique sous l'auth moderne**
       (ADR-010) : l'application charge l'utilisateur (`current_user`) puis pose
       ses rôles sur la requête (middleware) ; le RBAC contractuel les lit ici.
    2. session utilisateur **legacy** (dépréciée, ADR-012) → champ "roles".
    3. liste vide si rien trouvé.

    Ne lève jamais d'erreur si la requête ou la session est absente. N'appelle
    plus `core.security.session.get_user` (déprécié) : F30.
    """
    injected = getattr(request, "roles", None)
    if injected is not None:
        if isinstance(injected, list):
            return [r for r in cast("list[Any]", injected) if isinstance(r, str)]
        return []

    try:
        utilisateur = _legacy_session_user(request)
    except Exception:
        return []

    if utilisateur:
        roles = utilisateur.get("roles", [])
        if isinstance(roles, list):
            return [r for r in cast("list[Any]", roles) if isinstance(r, str)]
    return []


def require_contract_permission_for_request(
    request: Any,
    permission: str,
    project_root: str | Path = ".",
) -> Response | None:
    """Vérifie une permission contractuelle depuis la requête.

    Charge mvc/security/rbac.json depuis project_root, extrait les rôles
    de la requête et délègue à require_contract_permission.

    Retourne None si la permission est accordée.
    Retourne Response(403) si refusée, si le contrat est absent ou invalide.
    Ne modifie ni la requête ni aucun fichier.

    Usage dans un contrôleur :
        response = require_contract_permission_for_request(request, "article.delete")
        if response is not None:
            return response
    """
    result = load_rbac_contract(project_root)
    roles = get_request_roles(request)
    return require_contract_permission(result, roles, permission)


def contract_permission_required(
    permission: str,
    project_root: str | Path = ".",
) -> Callable[..., Any]:
    """Décorateur opt-in protégeant une action avec une permission contractuelle.

    Charge mvc/security/rbac.json depuis project_root et vérifie si la
    requête possède la permission déclarée. Retourne Response(403) si refusée.

    Usage :
        @contract_permission_required("article.delete")
        def delete(request, article_id):
            ...
    """
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(request: Any, *args: Any, **kwargs: Any) -> Any:
            response = require_contract_permission_for_request(request, permission, project_root)
            if response is not None:
                return response
            return func(request, *args, **kwargs)
        return wrapper
    return decorator
