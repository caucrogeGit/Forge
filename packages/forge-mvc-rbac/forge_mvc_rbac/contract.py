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

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


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
    errors: list[RbacContractError] = field(default_factory=list)
    data: dict[str, Any] | None = None


# ---------------------------------------------------------------------------
# Helpers internes
# ---------------------------------------------------------------------------


def _find_schemas_dir() -> Path | None:
    try:
        import forge_cli  # type: ignore[import-untyped]
        candidate = Path(forge_cli.__file__).resolve().parent / "schemas"
        if candidate.is_dir():
            return candidate
    except ImportError:
        pass
    return None


def _build_registry(schemas_dir: Path):
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        return None

    resources = []
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
        return Registry().with_resources(resources)
    except Exception:
        return None


def _make_validator(schemas_dir: Path, registry):
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


def _collect_errors(validator, instance: dict) -> list[RbacContractError]:
    errors = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: str(e.absolute_path)):
        path = "$." + ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "$"
        errors.append(RbacContractError(path=path, message=error.message))
    return errors


def _count_roles(instance: dict) -> int:
    roles = instance.get("roles")
    return len(roles) if isinstance(roles, dict) else 0


def _count_entities(instance: dict) -> int:
    entities = instance.get("entities")
    return len(entities) if isinstance(entities, dict) else 0


def _result_degraded(path_str: str, instance: dict) -> RbacContractResult:
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
