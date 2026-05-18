"""Commande forge schema:list — liste les schémas JSON Forge disponibles.

Lit le registre schemas/forge.schema.index.json et affiche chaque schéma
référencé avec son chemin relatif et son statut (OK / MANQUANT).

Options :
  --json  Sortie machine JSON stable (stdout uniquement, aucune ligne humaine).

Codes de retour :
  0  — registre lisible et tous les schémas présents
  1  — registre illisible OU au moins un schéma manquant
"""

from __future__ import annotations

import json
import sys
from pathlib import Path


def _schemas_dir() -> Path:
    return Path(__file__).resolve().parent


def _registry_path() -> Path:
    return _schemas_dir() / "forge.schema.index.json"


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


def schema_list_main(args: list[str]) -> None:
    json_output = "--json" in args

    unknown = [a for a in args if a != "--json"]
    if unknown:
        msg = f"option inconnue pour «schema:list» : {unknown[0]!r}"
        if json_output:
            print(json.dumps({"valid": False, "error": msg}, ensure_ascii=False))
        else:
            print(f"Erreur : {msg}", file=sys.stderr)
        sys.exit(1)

    registry, error = _load_registry()

    if registry is None:
        if json_output:
            print(json.dumps(
                {"valid": False, "error": error, "registry": "schemas/forge.schema.index.json"},
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

    entries: list[dict] = []
    any_missing = False
    for name, relative_path in schemas_dict.items():
        clean = relative_path.lstrip("./")
        exists = (schemas_dir / clean).exists()
        if not exists:
            any_missing = True
        entries.append({"name": name, "path": f"schemas/{clean}", "exists": exists})

    if json_output:
        print(json.dumps(
            {
                "valid": not any_missing,
                "registry": "schemas/forge.schema.index.json",
                "schema_version": schema_version,
                "count": len(entries),
                "schemas": entries,
            },
            indent=2,
            ensure_ascii=False,
        ))
        sys.exit(1 if any_missing else 0)

    if not entries:
        print("Aucun schéma référencé dans le registre.")
        return

    print("Schémas JSON Forge disponibles :\n")
    name_w = max(len(e["name"]) for e in entries)
    path_w = max(len(e["path"]) for e in entries)
    for entry in entries:
        status = "OK" if entry["exists"] else "MANQUANT"
        print(f"  - {entry['name'].ljust(name_w)}    {entry['path'].ljust(path_w)}    {status}")

    print(f"\nTotal : {len(entries)} schéma(s)")

    if any_missing:
        sys.exit(1)
