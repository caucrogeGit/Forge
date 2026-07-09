# pyright: strict
"""`forge entity:doc` — vue globale des entités et relations (Markdown + Mermaid).

Lit les contrats du projet (`mvc/entities/*.json` et `relations.json`) et produit
une documentation Markdown : un tableau par entité (champs, types, contraintes),
la liste des relations avec leur cardinalité, et un diagramme Mermaid `erDiagram`.

Commande de **lecture seule** : par défaut elle affiche sur stdout (mode « Forge
affiche », charte §7). `--output <fichier>` écrit le résultat (écrasement annoncé).
Aucun backend BDD ni connexion n'est requis : la vue vient des contrats.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from forge_mvc_entities.relations import (
    ValidatedCanonicalManyToManyRelation,
    ValidatedRelation,
    load_entity_definitions,
    validate_relations_definition,
)

_EMPTY_RELATIONS: dict[str, Any] = {"schema_version": "1.0", "relations": []}


def _yn(value: bool) -> str:
    return "oui" if value else "non"


def _mermaid_type(sql_type: str) -> str:
    """Type SQL simplifié pour un attribut Mermaid (un seul mot, sans parenthèses)."""
    return sql_type.split("(")[0].split()[0] or "TEXT"


def _entity_table(definition: dict[str, Any]) -> list[str]:
    lines = [
        f"### {definition['entity']} (`{definition['table']}`)",
        "",
        "| Champ | Colonne | Type SQL | Type Python | Nullable | PK | Unique |",
        "|---|---|---|---|---|---|---|",
    ]
    for field in definition["fields"]:
        lines.append(
            f"| {field['name']} | {field['column']} | {field['sql_type']} | "
            f"{field['python_type']} | {_yn(field.get('nullable', False))} | "
            f"{_yn(field.get('primary_key', False))} | {_yn(field.get('unique', False))} |"
        )
    lines.append("")
    return lines


def _relations_table(
    relations: list[ValidatedRelation | ValidatedCanonicalManyToManyRelation],
) -> list[str]:
    if not relations:
        return ["_Aucune relation déclarée._", ""]
    lines = [
        "| Source | Cible | Clé / Pivot | Cardinalité | ON DELETE |",
        "|---|---|---|---|---|",
    ]
    for rel in relations:
        if isinstance(rel, ValidatedRelation):
            lines.append(
                f"| {rel.from_entity} | {rel.to_entity} | `{rel.from_column}` | N:1 | {rel.on_delete} |"
            )
        else:
            lines.append(
                f"| {rel.from_entity} | {rel.to_entity} | `{rel.pivot_table}` (pivot) | N:N | {rel.on_delete} |"
            )
    lines.append("")
    return lines


def _mermaid_diagram(
    entity_map: dict[str, dict[str, Any]],
    relations: list[ValidatedRelation | ValidatedCanonicalManyToManyRelation],
) -> list[str]:
    lines = ["```mermaid", "erDiagram"]
    for definition in entity_map.values():
        table = definition["table"].upper()
        lines.append(f"    {table} {{")
        for field in definition["fields"]:
            key = " PK" if field.get("primary_key") else ""
            lines.append(f"        {_mermaid_type(field['sql_type'])} {field['column']}{key}")
        lines.append("    }")
    for rel in relations:
        if isinstance(rel, ValidatedRelation):
            # N côté source vers 1 côté cible ; « o » si la FK est optionnelle.
            left = "}o" if rel.fk_nullable else "}|"
            lines.append(f'    {rel.from_table.upper()} {left}--|| {rel.to_table.upper()} : "{rel.from_column}"')
        else:
            lines.append(f'    {rel.from_table.upper()} }}o--o{{ {rel.to_table.upper()} : "{rel.pivot_table}"')
    lines.append("```")
    lines.append("")
    return lines


def build_entity_doc(entities_root: Path) -> str:
    """Construit la documentation Markdown des entités et relations du projet."""
    entity_map = load_entity_definitions(entities_root)

    relations_path = entities_root / "relations.json"
    raw_relations: Any = _EMPTY_RELATIONS
    if relations_path.exists():
        raw_relations = json.loads(relations_path.read_text(encoding="utf-8"))
    relations = validate_relations_definition(
        raw_relations, source=str(relations_path), entities_root=entities_root
    )

    lines: list[str] = ["# Schéma des entités", ""]
    if not entity_map:
        lines.append("_Aucune entité déclarée dans mvc/entities/._")
        return "\n".join(lines) + "\n"

    lines += ["## Entités", ""]
    for name in sorted(entity_map):
        lines += _entity_table(entity_map[name])

    lines += ["## Relations", ""]
    lines += _relations_table(relations)

    lines += ["## Diagramme", ""]
    lines += _mermaid_diagram(entity_map, relations)

    return "\n".join(lines) + "\n"


def _parse_output(args: list[str]) -> str | None:
    for i, arg in enumerate(args):
        if arg == "--output":
            return args[i + 1] if i + 1 < len(args) else ""
        if arg.startswith("--output="):
            return arg.split("=", 1)[1]
    return None


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if any(a in {"-h", "--help"} for a in args):
        print((__doc__ or "").strip())
        raise SystemExit(0)

    entities_root = Path.cwd() / "mvc" / "entities"
    if not entities_root.is_dir():
        print("Erreur : dossier mvc/entities introuvable.", file=sys.stderr)
        print("Conseil : lancez forge entity:doc depuis la racine d'un projet Forge.", file=sys.stderr)
        raise SystemExit(1)

    output = _parse_output(args)
    if output == "":
        print("Erreur : --output attend un chemin de fichier.", file=sys.stderr)
        raise SystemExit(1)

    try:
        doc = build_entity_doc(entities_root)
    except (ValueError, OSError) as exc:
        print(f"[ERREUR] {exc}", file=sys.stderr)
        raise SystemExit(1)

    if output is None:
        print(doc, end="")
        return

    out_path = Path(output)
    existed = out_path.exists()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(doc, encoding="utf-8")
    verb = "Écrasé" if existed else "Écrit"
    print(f"[OK] {verb} : {out_path.as_posix()}")


if __name__ == "__main__":
    main()
