"""Commande forge entity:validate — validation JSON Schema + sémantique.

Valide les fichiers d'entités et de relations d'un projet Forge en deux passes :

1. Validation structurelle JSON Schema (entity.schema.json / relations.schema.json).
2. Validation sémantique Forge (doublons, noms réservés, cohérence relationnelle).

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
    """Retourne le dossier schemas/ de l'installation Forge."""
    return Path(__file__).resolve().parent.parent.parent / "schemas"


def _build_registry():
    """Charge tous les schémas locaux dans un registre referencing."""
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
    """Crée un Draft202012Validator pour le schéma donné."""
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


def _format_error(error) -> str:
    """Formate une erreur jsonschema en message humain."""
    path = "$"
    if error.absolute_path:
        path = "$." + ".".join(str(p) for p in error.absolute_path)
    return f"  Chemin : {path}\n  Raison : {error.message}"


def _collect_entity_files(entities_root: Path) -> Iterator[Path]:
    """Itère sur les fichiers d'entité, en excluant relations.json."""
    for f in sorted(entities_root.rglob("*.json")):
        if f.name == "relations.json":
            continue
        yield f


def main(args: list[str] | None = None) -> None:
    from forge_cli.entities.entity_semantic_validate import validate_semantic

    cwd = Path.cwd()
    entities_root = cwd / "mvc" / "entities"

    if not entities_root.is_dir():
        print("Erreur : dossier mvc/entities introuvable.", file=sys.stderr)
        print("Conseil : lancez forge entity:validate depuis la racine d'un projet Forge.", file=sys.stderr)
        sys.exit(1)

    try:
        import jsonschema  # noqa: F401
    except ImportError:
        print("Erreur : jsonschema n'est pas installé.", file=sys.stderr)
        print("Conseil : pip install jsonschema>=4.18", file=sys.stderr)
        sys.exit(1)

    registry, _ = _build_registry()
    if registry is None:
        print("Erreur : impossible de charger les schémas Forge.", file=sys.stderr)
        print(f"Conseil : vérifiez que {_schemas_dir()} est accessible.", file=sys.stderr)
        sys.exit(1)

    entity_validator = _make_validator(_ENTITY_SCHEMA_ID, registry)
    relations_validator = _make_validator(_RELATIONS_SCHEMA_ID, registry)

    if entity_validator is None:
        print("Erreur : schéma entity.schema.json introuvable.", file=sys.stderr)
        sys.exit(1)

    valid_count = 0
    error_count = 0
    valid_entities: list[tuple[str, dict]] = []
    valid_relations: dict | None = None

    # ── Passe 1 : validation structurelle JSON Schema ─────────────────────────

    entity_files = list(_collect_entity_files(entities_root))
    if not entity_files:
        print("Avertissement : aucun fichier d'entité trouvé dans mvc/entities/.")
    else:
        for entity_file in entity_files:
            rel_path = entity_file.relative_to(cwd)
            try:
                data = json.loads(entity_file.read_text(encoding="utf-8"))
            except json.JSONDecodeError as e:
                print(f"[ERREUR] {rel_path}")
                print(f"  Raison : JSON invalide — {e}")
                error_count += 1
                continue

            schema_errors = list(entity_validator.iter_errors(data))
            if schema_errors:
                print(f"[ERREUR] {rel_path}")
                for err in schema_errors:
                    print(_format_error(err))
                print("  Conseil : corrigez le fichier selon schemas/entity.schema.json.")
                error_count += 1
            else:
                entity_name = data.get("name", rel_path.stem)
                print(f"[OK] Entité {entity_name} valide.")
                valid_count += 1
                valid_entities.append((str(rel_path), data))

    relations_file = entities_root / "relations.json"
    if not relations_file.exists():
        print("Avertissement : mvc/entities/relations.json absent (optionnel).")
    elif relations_validator is None:
        print("Avertissement : schéma relations.schema.json introuvable — relations.json non validé.")
    else:
        rel_path = relations_file.relative_to(cwd)
        try:
            data = json.loads(relations_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            print(f"[ERREUR] {rel_path}")
            print(f"  Raison : JSON invalide — {e}")
            error_count += 1
            data = None

        if data is not None:
            schema_errors = list(relations_validator.iter_errors(data))
            if schema_errors:
                print(f"[ERREUR] {rel_path}")
                for err in schema_errors:
                    print(_format_error(err))
                print("  Conseil : corrigez le fichier selon schemas/relations.schema.json.")
                error_count += 1
            else:
                print("[OK] relations.json valide.")
                valid_count += 1
                valid_relations = data

    # ── Passe 2 : validation sémantique Forge ────────────────────────────────

    if valid_entities:
        semantic_errors = validate_semantic(valid_entities, valid_relations)
        if semantic_errors:
            print()
            print("[ERREUR] Validation sémantique")
            for sem_err in semantic_errors:
                print(f"  Fichier : {sem_err.source}")
                print(f"  Chemin  : {sem_err.path}")
                print(f"  Raison  : {sem_err.reason}")
                if sem_err.hint:
                    print(f"  Conseil : {sem_err.hint}")
                print()
            error_count += len(semantic_errors)

    print()
    if error_count == 0:
        print(f"Validation terminée : {valid_count} fichier{'s' if valid_count > 1 else ''} valide{'s' if valid_count > 1 else ''}, 0 erreur.")
        sys.exit(0)
    else:
        print(
            f"Validation terminée : {valid_count} fichier{'s' if valid_count > 1 else ''} valide{'s' if valid_count > 1 else ''}, "
            f"{error_count} erreur{'s' if error_count > 1 else ''}."
        )
        sys.exit(1)
