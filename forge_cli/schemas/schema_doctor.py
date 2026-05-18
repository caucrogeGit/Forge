"""Commande forge schema:doctor — diagnostique les schémas JSON Forge.

Vérifie pour chaque schéma référencé dans forge.schema.index.json :
  1. le fichier existe ;
  2. le fichier est du JSON valide ;
  3. la clé $schema est présente et pointe vers Draft 2020-12 ;
  4. la clé $id est présente ;
  5. les $ref locaux (hors '#' et 'http') pointent vers des fichiers existants.

Ne valide pas les entités utilisateur (mvc/entities/*.json) — c'est
le rôle de «forge entity:validate».

Options :
  --json  Sortie machine JSON stable (stdout uniquement, aucune ligne humaine).

Codes de retour :
  0  — aucune erreur
  1  — au moins une erreur (registre illisible, schéma absent/invalide, $ref mort)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


_DRAFT_2020_12 = "https://json-schema.org/draft/2020-12/schema"


def _forge_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent


def _schemas_dir() -> Path:
    return _forge_root() / "schemas"


def _registry_path() -> Path:
    return _schemas_dir() / "forge.schema.index.json"


def _collect_local_refs(obj: object, refs: set[str]) -> None:
    """Parcourt récursivement un objet JSON et collecte les $ref locaux.

    Un $ref est « local » s'il ne commence ni par '#' (interne) ni par
    'http' (URI distant). Forme attendue : 'file.schema.json' ou
    'file.schema.json#/$defs/quelquechose'.
    """
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "$ref" and isinstance(value, str):
                if not value.startswith("#") and not value.startswith("http"):
                    filename = value.split("#")[0]
                    if filename:
                        refs.add(filename)
            else:
                _collect_local_refs(value, refs)
    elif isinstance(obj, list):
        for item in obj:
            _collect_local_refs(item, refs)


def _load_registry() -> tuple[dict, None] | tuple[None, str]:
    """Retourne (registre, None) si OK, (None, message_erreur) sinon."""
    path = _registry_path()
    if not path.exists():
        return None, "registre des schémas Forge introuvable"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return None, f"registre des schémas Forge invalide : {exc}"
    if not isinstance(data.get("schemas"), dict):
        return None, "clé 'schemas' absente ou invalide dans le registre"
    return data, None


def schema_doctor_main(args: list[str]) -> None:
    json_output = "--json" in args

    unknown = [a for a in args if a != "--json"]
    if unknown:
        msg = f"option inconnue pour «schema:doctor» : {unknown[0]!r}"
        if json_output:
            print(json.dumps({"valid": False, "error": msg}, ensure_ascii=False))
        else:
            print(f"Erreur : {msg}", file=sys.stderr)
        sys.exit(1)

    registry, error = _load_registry()

    if registry is None:
        if json_output:
            print(json.dumps(
                {
                    "valid": False,
                    "error": error,
                    "registry": "schemas/forge.schema.index.json",
                    "errors": [error],
                },
                ensure_ascii=False,
            ))
        else:
            print(f"Erreur : {error}.", file=sys.stderr)
            if "introuvable" in (error or ""):
                print("Chemin attendu : schemas/forge.schema.index.json", file=sys.stderr)
        sys.exit(1)

    schemas_dir = _schemas_dir()
    schemas_dict: dict[str, str] = registry["schemas"]
    schema_version: str = registry.get("schema_version", "?")

    errors: list[str] = []
    warnings: list[str] = []
    schemas_result: list[dict] = []
    refs_result: list[dict] = []

    if not isinstance(registry.get("schema_version"), str):
        errors.append("clé 'schema_version' absente ou non textuelle dans le registre")

    for name, relative_path in schemas_dict.items():
        clean = relative_path.lstrip("./")
        display_path = f"schemas/{clean}"
        abs_path = schemas_dir / clean

        entry: dict = {
            "name": name,
            "path": display_path,
            "exists": False,
            "json_valid": False,
            "schema_draft": None,
            "id": None,
        }

        if not abs_path.exists():
            errors.append(f"{display_path} : fichier manquant")
            schemas_result.append(entry)
            continue

        entry["exists"] = True

        try:
            schema_obj = json.loads(abs_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"{display_path} : JSON invalide ({exc})")
            schemas_result.append(entry)
            continue

        entry["json_valid"] = True

        schema_decl: str | None = schema_obj.get("$schema")
        if not schema_decl:
            errors.append(f"{display_path} : clé '$schema' absente")
        else:
            entry["schema_draft"] = schema_decl
            if schema_decl != _DRAFT_2020_12:
                errors.append(
                    f"{display_path} : '$schema' attendu '{_DRAFT_2020_12}', trouvé '{schema_decl}'"
                )

        schema_id: str | None = schema_obj.get("$id")
        if not schema_id:
            errors.append(f"{display_path} : clé '$id' absente")
        else:
            entry["id"] = schema_id

        local_refs: set[str] = set()
        _collect_local_refs(schema_obj, local_refs)
        for ref_filename in sorted(local_refs):
            ref_abs = schemas_dir / ref_filename
            ref_exists = ref_abs.exists()
            refs_result.append(
                {
                    "source": display_path,
                    "ref": ref_filename,
                    "resolved": f"schemas/{ref_filename}",
                    "exists": ref_exists,
                }
            )
            if not ref_exists:
                errors.append(f"{display_path} : $ref local '{ref_filename}' introuvable")

        schemas_result.append(entry)

    schemas_checked = len(schemas_dict)
    all_ok = len(errors) == 0

    if json_output:
        print(json.dumps(
            {
                "valid": all_ok,
                "registry": "schemas/forge.schema.index.json",
                "schema_version": schema_version,
                "schemas_checked": schemas_checked,
                "errors_count": len(errors),
                "warnings_count": len(warnings),
                "schemas": schemas_result,
                "references": refs_result,
                "errors": errors,
                "warnings": warnings,
            },
            indent=2,
            ensure_ascii=False,
        ))
        sys.exit(0 if all_ok else 1)

    print("Diagnostic des schémas JSON Forge\n")
    print(f"Registre : schemas/forge.schema.index.json")
    print(f"Version  : {schema_version}\n")

    print("Schémas :")
    name_w = max((len(e["name"]) for e in schemas_result), default=4)
    path_w = max((len(e["path"]) for e in schemas_result), default=10)
    for entry in schemas_result:
        if not entry["exists"]:
            status = "MANQUANT"
        elif not entry["json_valid"]:
            status = "JSON INVALIDE"
        elif not entry.get("schema_draft"):
            status = "$schema ABSENT"
        elif not entry.get("id"):
            status = "$id ABSENT"
        else:
            status = "OK"
        print(f"  - {entry['name'].ljust(name_w)}    {entry['path'].ljust(path_w)}    {status}")

    if refs_result:
        print("\nRéférences locales :")
        src_w = max(len(r["source"]) for r in refs_result)
        ref_w = max(len(r["ref"]) for r in refs_result)
        for ref in refs_result:
            status = "OK" if ref["exists"] else "MANQUANT"
            print(f"  - {ref['source'].ljust(src_w)}  ->  {ref['ref'].ljust(ref_w)}    {status}")

    if all_ok:
        print(f"\nRésultat : OK — {schemas_checked} schéma(s), 0 erreur.")
    else:
        print(f"\nRésultat : ERREUR — {len(errors)} erreur(s).")
        for msg in errors:
            print(f"  - {msg}")
        print("Conseil : corrigez les fichiers schemas/*.schema.json ou le registre.")

    sys.exit(0 if all_ok else 1)
