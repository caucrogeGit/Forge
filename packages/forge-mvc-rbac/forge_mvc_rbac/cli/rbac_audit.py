# pyright: strict
"""Commande forge rbac:audit — audit de cohérence de mvc/security/rbac.json.

Vérifie la cohérence fonctionnelle du contrat RBAC : rôles sans permissions,
entités sans actions CRUD, permissions non déclarées dans les entités ou
inutilisées par les rôles. Le fichier est optionnel : son absence n'est pas
une erreur.

Options :
  --json  Sortie machine JSON (stdout uniquement, aucune ligne humaine).

Codes de retour :
  0  — fichier absent OU fichier valide (avec ou sans avertissements)
  1  — fichier présent mais invalide (JSON ou schéma) OU option inconnue
"""

from __future__ import annotations

import json
from typing import Any, cast
import sys
from pathlib import Path


_RBAC_SCHEMA_ID = "https://forge-mvc.dev/schemas/rbac.schema.json"
_RBAC_CONTRACT_PATH = Path("mvc") / "security" / "rbac.json"
_CRUD_ACTIONS = ("list", "show", "create", "update", "delete")


def _schemas_dir() -> Path:
    return Path(__file__).resolve().parent.parent / "schemas"


def _build_registry() -> "tuple[Any, Any]":
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        return None, None

    schemas_dir = _schemas_dir()
    if not schemas_dir.is_dir():
        return None, None

    resources: list[Any] = []
    for f in schemas_dir.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            if "$id" in schema:
                resources.append(
                    (schema["$id"], Resource.from_contents(schema, default_specification=DRAFT202012))
                )
        except Exception:
            pass

    try:
        return cast("Any", Registry()).with_resources(resources), DRAFT202012  # pyright: ignore[reportUnknownArgumentType]  # défaut _anchors interne à referencing
    except Exception:
        return None, None


def _make_validator(registry: Any) -> Any:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return None

    schemas_dir = _schemas_dir()
    for f in schemas_dir.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            if schema.get("$id") == _RBAC_SCHEMA_ID:
                return Draft202012Validator(schema, registry=registry)
        except Exception:
            pass
    return None


def _collect_schema_errors(validator: Any, instance: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: str(e.absolute_path)):
        path = "$." + ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "$"
        errors.append({"path": path, "message": error.message})
    return errors


def _audit_warnings(instance: dict[str, Any]) -> list[dict[str, Any]]:
    """Retourne les avertissements de cohérence fonctionnelle du contrat."""
    warnings: list[dict[str, Any]] = []
    roles = instance.get("roles")
    entities = instance.get("entities")

    if not isinstance(roles, dict) or len(cast("dict[str, Any]", roles)) == 0:
        warnings.append({
            "code": "missing_roles",
            "message": "Aucun rôle déclaré dans le contrat RBAC.",
        })

    if not isinstance(entities, dict) or len(cast("dict[str, Any]", entities)) == 0:
        warnings.append({
            "code": "missing_entities",
            "message": "Aucune entité déclarée dans le contrat RBAC.",
        })

    # Collect all permissions declared in entities: permission_code → (entity, action)
    declared_permissions: dict[str, tuple[str, str]] = {}
    if isinstance(entities, dict):
        for entity_name, entity_data in cast("dict[str, Any]", entities).items():
            if not isinstance(entity_data, dict):
                continue
            perms = cast("dict[str, Any]", entity_data).get("permissions", {})
            if not isinstance(perms, dict) or len(cast("dict[str, Any]", perms)) == 0:
                warnings.append({
                    "code": "entity_without_permissions",
                    "entity": entity_name,
                    "message": f"L'entité '{entity_name}' n'a aucune permission déclarée.",
                })
                continue
            for action, perm_code in cast("dict[str, Any]", perms).items():
                if isinstance(perm_code, str):
                    declared_permissions[perm_code] = (entity_name, action)
            for action in _CRUD_ACTIONS:
                if action not in perms:
                    warnings.append({
                        "code": "missing_crud_action",
                        "entity": entity_name,
                        "action": action,
                        "message": f"L'entité '{entity_name}' n'a pas d'action CRUD '{action}'.",
                    })

    # Collect permissions assigned to roles
    assigned_permissions: set[str] = set()
    if isinstance(roles, dict):
        for role_name, role_perms in cast("dict[str, Any]", roles).items():
            if not isinstance(role_perms, list) or len(cast("list[Any]", role_perms)) == 0:
                warnings.append({
                    "code": "empty_role",
                    "role": role_name,
                    "message": f"Le rôle '{role_name}' n'a aucune permission.",
                })
                continue
            for perm in cast("list[Any]", role_perms):
                if isinstance(perm, str):
                    assigned_permissions.add(perm)
                    if declared_permissions and perm not in declared_permissions:
                        warnings.append({
                            "code": "role_permission_not_declared",
                            "role": role_name,
                            "permission": perm,
                            "message": (
                                f"La permission '{perm}' du rôle '{role_name}'"
                                " n'est déclarée dans aucune entité."
                            ),
                        })

    # Check entity permissions not assigned to any role
    if assigned_permissions and isinstance(entities, dict):
        for entity_name, entity_data in cast("dict[str, Any]", entities).items():
            if not isinstance(entity_data, dict):
                continue
            perms = cast("dict[str, Any]", entity_data).get("permissions", {})
            if not isinstance(perms, dict):
                continue
            for action, perm_code in cast("dict[str, Any]", perms).items():
                if isinstance(perm_code, str) and perm_code not in assigned_permissions:
                    warnings.append({
                        "code": "entity_permission_unused",
                        "entity": entity_name,
                        "action": action,
                        "permission": perm_code,
                        "message": (
                            f"La permission '{perm_code}' de l'entité '{entity_name}'"
                            " n'est assignée à aucun rôle."
                        ),
                    })

    return warnings


def rbac_audit_main(args: list[str]) -> None:
    use_json = "--json" in (args or [])

    unknown = [a for a in (args or []) if a != "--json"]
    if unknown:
        msg = f"option inconnue pour «rbac:audit» : {unknown[0]!r}"
        if use_json:
            print(json.dumps({"valid": False, "error": msg}, ensure_ascii=False))
        else:
            print(f"Erreur : {msg}", file=sys.stderr)
        sys.exit(1)

    cwd = Path.cwd()
    rbac_path = cwd / _RBAC_CONTRACT_PATH
    path_str = str(_RBAC_CONTRACT_PATH)

    if not rbac_path.exists():
        if use_json:
            print(json.dumps({
                "valid": True,
                "exists": False,
                "path": path_str,
                "errors_count": 0,
                "warnings_count": 0,
                "errors": [],
                "warnings": [],
            }, ensure_ascii=False))
        else:
            print(f"Aucun contrat RBAC trouvé : {path_str}")
            print("Le RBAC est optionnel. Créez mvc/security/rbac.json pour l'activer.")
        sys.exit(0)

    try:
        instance = json.loads(rbac_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Fichier JSON invalide : {exc}"
        if use_json:
            print(json.dumps({
                "valid": False,
                "exists": True,
                "path": path_str,
                "errors_count": 1,
                "warnings_count": 0,
                "errors": [{"path": "$", "message": msg}],
                "warnings": [],
            }, ensure_ascii=False))
        else:
            print(f"Erreur : {msg}", file=sys.stderr)
        sys.exit(1)

    registry, _ = _build_registry()
    if registry is None:
        msg = "Impossible de charger les schémas Forge."
        if use_json:
            print(json.dumps({"valid": False, "error": msg}, ensure_ascii=False))
        else:
            print(f"Erreur : {msg}", file=sys.stderr)
        sys.exit(1)

    validator = _make_validator(registry)
    if validator is None:
        msg = "Schéma rbac.schema.json introuvable dans forge_mvc_rbac/schemas/."
        if use_json:
            print(json.dumps({"valid": False, "error": msg}, ensure_ascii=False))
        else:
            print(f"Erreur : {msg}", file=sys.stderr)
        sys.exit(1)

    schema_errors = _collect_schema_errors(validator, instance)
    roles_count = len(instance.get("roles", {})) if isinstance(instance.get("roles"), dict) else 0
    entities_count = len(instance.get("entities", {})) if isinstance(instance.get("entities"), dict) else 0

    if schema_errors:
        if use_json:
            print(json.dumps({
                "valid": False,
                "exists": True,
                "path": path_str,
                "roles_count": roles_count,
                "entities_count": entities_count,
                "errors_count": len(schema_errors),
                "warnings_count": 0,
                "errors": schema_errors,
                "warnings": [],
            }, indent=2, ensure_ascii=False))
        else:
            print(f"Contrat RBAC invalide : {path_str}", file=sys.stderr)
            for err in schema_errors:
                print(f"  - {err['path']} : {err['message']}", file=sys.stderr)
        sys.exit(1)

    warnings = _audit_warnings(instance)

    if use_json:
        print(json.dumps({
            "valid": True,
            "exists": True,
            "path": path_str,
            "roles_count": roles_count,
            "entities_count": entities_count,
            "errors_count": 0,
            "warnings_count": len(warnings),
            "errors": [],
            "warnings": warnings,
        }, indent=2, ensure_ascii=False))
    else:
        print(f"Contrat RBAC : {path_str}")
        if roles_count:
            print(f"Rôles     : {roles_count}")
        if entities_count:
            print(f"Entités   : {entities_count}")
        if warnings:
            print(f"Avertissements ({len(warnings)}) :")
            for w in warnings:
                print(f"  - [{w['code']}] {w['message']}")
        else:
            print("Aucun avertissement.")
        print("Résultat  : OK")

    sys.exit(0)
