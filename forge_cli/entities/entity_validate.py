"""Commande forge entity:validate — validation JSON Schema + sémantique.

Valide les fichiers d'entités et de relations d'un projet Forge en deux passes :

1. Validation structurelle JSON Schema (entity.schema.json / relations.schema.json).
2. Validation sémantique Forge (doublons, noms réservés, cohérence relationnelle).

Options :
  --json  Sortie machine JSON stable (stdout uniquement, aucune ligne humaine).

Prérequis : jsonschema >= 4.18 (pip install jsonschema).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Iterator


_ENTITY_SCHEMA_ID = "https://forge-mvc.dev/schemas/entity.schema.json"
_RELATIONS_SCHEMA_ID = "https://forge-mvc.dev/schemas/relations.schema.json"


def _schemas_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "schemas"


def _build_registry():
    try:
        from referencing import Registry, Resource
        from referencing.jsonschema import DRAFT202012
    except ImportError:
        return None, None

    schemas_dir = _schemas_dir()
    if not schemas_dir.is_dir():
        return None, None

    resources = []
    for f in schemas_dir.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            if "$id" in schema:
                resources.append(
                    (schema["$id"], Resource.from_contents(schema, default_specification=DRAFT202012))
                )
        except (json.JSONDecodeError, Exception):
            pass

    return Registry().with_resources(resources), DRAFT202012


def _make_validator(schema_id: str, registry):
    from jsonschema import Draft202012Validator
    schemas_dir = _schemas_dir()
    for f in schemas_dir.glob("*.json"):
        try:
            schema = json.loads(f.read_text(encoding="utf-8"))
            if schema.get("$id") == schema_id:
                return Draft202012Validator(schema, registry=registry)
        except Exception:
            pass
    return None


def _schema_error_path(error) -> str:
    if error.absolute_path:
        return "$." + ".".join(str(p) for p in error.absolute_path)
    return "$"


def _collect_entity_files(entities_root: Path) -> Iterator[Path]:
    for f in sorted(entities_root.rglob("*.json")):
        if f.name == "relations.json":
            continue
        yield f


def _collect_results(
    cwd: Path,
    entities_root: Path,
    entity_validator,
    relations_validator,
    validate_semantic,
    codes: dict,
) -> dict:
    """Exécute les deux passes de validation et retourne les résultats structurés.

    Returns:
        dict avec : files_checked, files_valid, errors (liste plate), warnings,
                    human_events (liste ordonnée pour affichage humain).
    """
    all_errors: list[dict] = []
    warnings: list[str] = []
    # human_events : liste ordonnée d'événements pour l'affichage humain
    # types : "ok", "file_errors", "warning"
    human_events: list[dict] = []
    files_checked = 0
    files_valid = 0
    valid_entities: list[tuple[str, dict]] = []
    valid_relations: dict | None = None

    # ── Passe 1 : validation structurelle JSON Schema ─────────────────────────

    entity_files = list(_collect_entity_files(entities_root))
    if not entity_files:
        msg = "Aucun fichier d'entité trouvé dans mvc/entities/."
        warnings.append(msg)
        human_events.append({"type": "warning", "message": msg})
    else:
        for entity_file in entity_files:
            rel_path = entity_file.relative_to(cwd)
            rel_str = str(rel_path)
            files_checked += 1
            try:
                data = json.loads(entity_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                err = {
                    "code": codes["JSON_INVALID"],
                    "file": rel_str,
                    "path": "$",
                    "message": f"JSON invalide — {e}",
                    "hint": "Vérifiez la syntaxe JSON du fichier.",
                    "phase": "json",
                }
                all_errors.append(err)
                human_events.append({"type": "file_errors", "file": rel_str, "errors": [err]})
                continue

            schema_errs = list(entity_validator.iter_errors(data))
            if schema_errs:
                file_errs = [
                    {
                        "code": codes["ENTITY_SCHEMA_INVALID"],
                        "file": rel_str,
                        "path": _schema_error_path(e),
                        "message": e.message,
                        "hint": "Corrigez le fichier selon schemas/entity.schema.json.",
                        "phase": "schema",
                    }
                    for e in schema_errs
                ]
                all_errors.extend(file_errs)
                human_events.append({"type": "file_errors", "file": rel_str, "errors": file_errs})
            else:
                entity_name = data.get("name", rel_path.stem)
                files_valid += 1
                valid_entities.append((rel_str, data))
                human_events.append({"type": "ok", "message": f"[OK] Entité {entity_name} valide."})

    relations_file = entities_root / "relations.json"
    if not relations_file.exists():
        msg = "mvc/entities/relations.json absent (optionnel)."
        warnings.append(msg)
        human_events.append({"type": "warning", "message": msg})
    elif relations_validator is None:
        msg = "Schéma relations.schema.json introuvable — relations.json non validé."
        warnings.append(msg)
        human_events.append({"type": "warning", "message": msg})
    else:
        rel_path = relations_file.relative_to(cwd)
        rel_str = str(rel_path)
        files_checked += 1
        try:
            data = json.loads(relations_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            err = {
                "code": codes["JSON_INVALID"],
                "file": rel_str,
                "path": "$",
                "message": f"JSON invalide — {e}",
                "hint": "Vérifiez la syntaxe JSON du fichier.",
                "phase": "json",
            }
            all_errors.append(err)
            human_events.append({"type": "file_errors", "file": rel_str, "errors": [err]})
            data = None

        if data is not None:
            schema_errs = list(relations_validator.iter_errors(data))
            if schema_errs:
                file_errs = [
                    {
                        "code": codes["RELATION_SCHEMA_INVALID"],
                        "file": rel_str,
                        "path": _schema_error_path(e),
                        "message": e.message,
                        "hint": "Corrigez le fichier selon schemas/relations.schema.json.",
                        "phase": "schema",
                    }
                    for e in schema_errs
                ]
                all_errors.extend(file_errs)
                human_events.append({"type": "file_errors", "file": rel_str, "errors": file_errs})
            else:
                files_valid += 1
                valid_relations = data
                human_events.append({"type": "ok", "message": "[OK] relations.json valide."})

    # ── Passe 2 : validation sémantique Forge ────────────────────────────────

    if valid_entities:
        semantic_errors = validate_semantic(valid_entities, valid_relations)
        for sem_err in semantic_errors:
            all_errors.append({
                "code": sem_err.code,
                "file": sem_err.file,
                "path": sem_err.path,
                "message": sem_err.message,
                "hint": sem_err.hint,
                "phase": "semantic",
            })

    return {
        "files_checked": files_checked,
        "files_valid": files_valid,
        "errors": all_errors,
        "warnings": warnings,
        "human_events": human_events,
    }


def _print_human(results: dict) -> None:
    errors = results["errors"]
    human_events = results["human_events"]
    files_valid = results["files_valid"]

    # Événements ordonnés (schema/json/ok/warning)
    for event in human_events:
        t = event["type"]
        if t == "ok":
            print(event["message"])
        elif t == "warning":
            print(f"Avertissement : {event['message']}")
        elif t == "file_errors":
            file_errs = event["errors"]
            print(f"[ERREUR] {event['file']}")
            print(f"  Code : {file_errs[0]['code']}")
            for err in file_errs:
                print(f"  Chemin : {err['path']}")
                print(f"  Raison : {err['message']}")
            print(f"  Conseil : {file_errs[0]['hint']}")

    # Erreurs sémantiques
    semantic_errors = [e for e in errors if e["phase"] == "semantic"]
    if semantic_errors:
        print()
        print("[ERREUR] Validation sémantique")
        for sem in semantic_errors:
            print(f"  Fichier : {sem['file']}")
            print(f"  Code : {sem['code']}")
            print(f"  Chemin  : {sem['path']}")
            print(f"  Raison  : {sem['message']}")
            if sem.get("hint"):
                print(f"  Conseil : {sem['hint']}")
            print()

    error_count = len(errors)
    s_f = "s" if files_valid > 1 else ""
    s_e = "s" if error_count > 1 else ""
    print()
    if error_count == 0:
        print(f"Validation terminée : {files_valid} fichier{s_f} valide{s_f}, 0 erreur.")
    else:
        print(f"Validation terminée : {files_valid} fichier{s_f} valide{s_f}, {error_count} erreur{s_e}.")


def main(args: list[str] | None = None) -> None:
    from forge_cli.entities.entity_semantic_validate import validate_semantic
    from forge_cli.entities.entity_validation_errors import (
        FORGE_ENTITY_JSON_INVALID,
        FORGE_ENTITY_SCHEMA_INVALID,
        FORGE_ENTITY_SCHEMA_MISSING,
        FORGE_RELATION_SCHEMA_INVALID,
    )

    use_json = "--json" in (args or [])
    cwd = Path.cwd()
    entities_root = cwd / "mvc" / "entities"

    if not entities_root.is_dir():
        if use_json:
            print(json.dumps({
                "valid": False,
                "files_checked": 0, "files_valid": 0,
                "errors_count": 1, "warnings_count": 0,
                "errors": [{"code": FORGE_ENTITY_SCHEMA_MISSING, "file": "", "path": "$",
                            "message": "dossier mvc/entities introuvable.",
                            "hint": "Lancez forge entity:validate depuis la racine d'un projet Forge.",
                            "phase": "runtime"}],
                "warnings": [],
            }))
        else:
            print("Erreur : dossier mvc/entities introuvable.", file=sys.stderr)
            print("Conseil : lancez forge entity:validate depuis la racine d'un projet Forge.", file=sys.stderr)
        sys.exit(1)

    try:
        import jsonschema  # noqa: F401
    except ImportError:
        if not use_json:
            print("Erreur : jsonschema n'est pas installé.", file=sys.stderr)
            print("Conseil : pip install jsonschema>=4.18", file=sys.stderr)
        sys.exit(1)

    registry, _ = _build_registry()
    if registry is None:
        if not use_json:
            print(f"  Code : {FORGE_ENTITY_SCHEMA_MISSING}", file=sys.stderr)
            print("Erreur : impossible de charger les schémas Forge.", file=sys.stderr)
            print(f"Conseil : vérifiez que {_schemas_dir()} est accessible.", file=sys.stderr)
        sys.exit(1)

    entity_validator = _make_validator(_ENTITY_SCHEMA_ID, registry)
    relations_validator = _make_validator(_RELATIONS_SCHEMA_ID, registry)

    if entity_validator is None:
        if not use_json:
            print(f"  Code : {FORGE_ENTITY_SCHEMA_MISSING}", file=sys.stderr)
            print("Erreur : schéma entity.schema.json introuvable.", file=sys.stderr)
        sys.exit(1)

    codes = {
        "JSON_INVALID": FORGE_ENTITY_JSON_INVALID,
        "ENTITY_SCHEMA_INVALID": FORGE_ENTITY_SCHEMA_INVALID,
        "RELATION_SCHEMA_INVALID": FORGE_RELATION_SCHEMA_INVALID,
    }

    results = _collect_results(
        cwd, entities_root, entity_validator, relations_validator, validate_semantic, codes
    )

    if use_json:
        errors = results["errors"]
        warnings = results["warnings"]
        output = {
            "valid": len(errors) == 0,
            "files_checked": results["files_checked"],
            "files_valid": results["files_valid"],
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    else:
        _print_human(results)

    sys.exit(0 if not results["errors"] else 1)
