# pyright: strict
"""Commande forge rbac:validate — valide mvc/security/rbac.json.

Vérifie que le contrat RBAC du projet respecte schemas/rbac.schema.json.
Le fichier est optionnel : son absence n'est pas une erreur.

Options :
  --json  Sortie machine JSON (stdout uniquement, aucune ligne humaine).

Codes de retour :
  0  — fichier absent (RBAC optionnel) OU fichier valide
  1  — fichier présent mais invalide OU erreur de chargement du schéma
"""

from __future__ import annotations

import json
from typing import Any, cast
import sys
from pathlib import Path


_RBAC_SCHEMA_ID = "https://forge-mvc.dev/schemas/rbac.schema.json"
_RBAC_CONTRACT_PATH = Path("mvc") / "security" / "rbac.json"


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


def _collect_errors(validator: Any, instance: dict[str, Any]) -> list[dict[str, Any]]:
    errors: list[dict[str, Any]] = []
    for error in sorted(validator.iter_errors(instance), key=lambda e: str(e.absolute_path)):
        path = "$." + ".".join(str(p) for p in error.absolute_path) if error.absolute_path else "$"
        errors.append({"path": path, "message": error.message})
    return errors


def rbac_validate_main(args: list[str]) -> None:
    use_json = "--json" in (args or [])

    unknown = [a for a in (args or []) if a != "--json"]
    if unknown:
        msg = f"option inconnue pour «rbac:validate» : {unknown[0]!r}"
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
                "errors": [],
            }, ensure_ascii=False))
        else:
            print(f"Aucun contrat RBAC trouvé : {path_str}")
            print("Le RBAC est optionnel. Créez mvc/security/rbac.json pour l'activer.")
        sys.exit(0)

    try:
        raw_text = rbac_path.read_text(encoding="utf-8")
        instance = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        msg = f"Fichier JSON invalide : {exc}"
        if use_json:
            print(json.dumps({
                "valid": False,
                "exists": True,
                "path": path_str,
                "errors_count": 1,
                "errors": [{"path": "$", "message": msg}],
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

    errors = _collect_errors(validator, instance)
    is_valid = len(errors) == 0

    roles_count = len(instance.get("roles", {})) if isinstance(instance.get("roles"), dict) else 0
    entities_count = len(instance.get("entities", {})) if isinstance(instance.get("entities"), dict) else 0

    if use_json:
        print(json.dumps({
            "valid": is_valid,
            "exists": True,
            "path": path_str,
            "schema": "forge_mvc_rbac/schemas/rbac.schema.json",
            "roles_count": roles_count,
            "entities_count": entities_count,
            "errors_count": len(errors),
            "errors": errors,
        }, indent=2, ensure_ascii=False))
    else:
        status = "OK" if is_valid else "ERREUR"
        if is_valid:
            print(f"Contrat RBAC valide : {path_str}")
            if roles_count:
                print(f"Rôles     : {roles_count}")
            if entities_count:
                print(f"Entités   : {entities_count}")
        else:
            print(f"Contrat RBAC invalide : {path_str}", file=sys.stderr)
            for err in errors:
                print(f"  - {err['path']} : {err['message']}", file=sys.stderr)
        print(f"Résultat  : {status}")

    sys.exit(0 if is_valid else 1)
