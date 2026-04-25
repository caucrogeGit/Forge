#!/usr/bin/env python3
"""
Ajoute une relation Forge dans mvc/entities/relations.json.

Usage :
    forge make:relation
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Callable, Any

from forge_cli.entities.make_entity import entities_dir, to_snake
from forge_cli.entities.relations import (
    ALLOWED_ACTIONS,
    ALLOWED_RELATION_TYPES,
    EntityRelationsError,
    load_entity_definitions,
    validate_relations_definition,
)
from forge_cli.entities.validation import EntityDefinitionError


def _prompt_text(
    label: str,
    *,
    default: str | None = None,
    allow_empty: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    if input_fn is None:
        input_fn = input
    prompt = label
    if default not in {None, ""}:
        prompt += f" [{default}]"
    prompt += " : "

    while True:
        value = input_fn(prompt).strip()
        if value:
            return value
        if default is not None:
            return default
        if allow_empty:
            return ""
        print("Une valeur est requise.")


def _prompt_yes_no(
    label: str,
    *,
    default: bool = False,
    input_fn: Callable[[str], str] | None = None,
) -> bool:
    if input_fn is None:
        input_fn = input
    suffix = "[O/n]" if default else "[o/N]"
    while True:
        value = input_fn(f"{label} {suffix} : ").strip().lower()
        if not value:
            return default
        if value in {"o", "oui", "y", "yes"}:
            return True
        if value in {"n", "non", "no"}:
            return False
        print("Réponse attendue : o ou n.")


def _prompt_relation_type(*, input_fn: Callable[[str], str] | None = None) -> str:
    if input_fn is None:
        input_fn = input
    default = "many_to_one"
    help_text = (
        "Type de relation "
        "[many_to_one ; many_to_many = entité pivot explicite + 2 many_to_one]"
    )
    while True:
        value = _prompt_text(help_text, default=default, input_fn=input_fn).strip().lower()
        if value in ALLOWED_RELATION_TYPES:
            return value
        if value == "many_to_many":
            print(
                "Forge V1 ne supporte pas many_to_many directement. "
                "Créez une entité pivot explicite, puis deux relations many_to_one."
            )
            continue
        print("Type de relation invalide. Valeur supportée en V1 : many_to_one.")


def _prompt_entity(
    label: str,
    entity_names: list[str],
    *,
    default: str | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    help_label = f"{label} ({', '.join(entity_names)})"
    while True:
        value = _prompt_text(help_label, default=default, input_fn=input_fn)
        if value in entity_names:
            return value
        print(f"Entité inconnue. Valeurs disponibles : {', '.join(entity_names)}.")


def _prompt_field(
    label: str,
    field_names: list[str],
    *,
    default: str | None = None,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    help_label = f"{label} ({', '.join(field_names)})"
    while True:
        value = _prompt_text(help_label, default=default, input_fn=input_fn)
        if value in field_names:
            return value
        print(f"Champ inconnu. Valeurs disponibles : {', '.join(field_names)}.")


def _prompt_action(
    label: str,
    *,
    default: str,
    input_fn: Callable[[str], str] | None = None,
) -> str:
    allowed = sorted(ALLOWED_ACTIONS)
    help_label = f"{label} ({', '.join(allowed)})"
    while True:
        value = _prompt_text(help_label, default=default, input_fn=input_fn).upper()
        if value in ALLOWED_ACTIONS:
            return value
        print(f"Valeur invalide. Valeurs supportées : {', '.join(allowed)}.")


def _load_relations_document(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"format_version": 1, "relations": []}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(
            f"{path.as_posix()}: JSON invalide ({exc.msg} à la ligne {exc.lineno}, colonne {exc.colno})"
        ) from exc

    if not isinstance(data, dict):
        raise ValueError(f"{path.as_posix()}: la racine doit être un objet JSON")
    if "format_version" not in data:
        raise ValueError(f"{path.as_posix()}: format_version manquant")
    if "relations" not in data:
        raise ValueError(f"{path.as_posix()}: relations manquant")
    if not isinstance(data["relations"], list):
        raise ValueError(f"{path.as_posix()}: relations doit être une liste")
    return data


def _build_relation_interactively(
    entity_map: dict[str, dict[str, Any]],
    *,
    input_fn: Callable[[str], str] | None = None,
) -> dict[str, str]:
    entity_names = sorted(entity_map)
    relation_type = _prompt_relation_type(input_fn=input_fn)
    from_entity = _prompt_entity("Entité source (porte la FK)", entity_names, input_fn=input_fn)
    to_entity = _prompt_entity("Entité cible (porte la PK visée)", entity_names, input_fn=input_fn)

    from_fields = [field["name"] for field in entity_map[from_entity]["fields"]]
    to_fields = [field["name"] for field in entity_map[to_entity]["fields"]]

    default_from_field = f"{to_snake(to_entity)}_id"
    if default_from_field not in from_fields:
        default_from_field = None
    default_to_field = "id" if "id" in to_fields else None

    from_field = _prompt_field(
        "Champ source from_field",
        from_fields,
        default=default_from_field,
        input_fn=input_fn,
    )
    to_field = _prompt_field(
        "Champ cible to_field",
        to_fields,
        default=default_to_field,
        input_fn=input_fn,
    )

    default_relation_name = f"{to_snake(from_entity)}_{to_snake(to_entity)}"
    relation_name = _prompt_text("Nom de la relation", default=default_relation_name, input_fn=input_fn)
    foreign_key_name = _prompt_text(
        "Nom de la contrainte SQL foreign_key_name",
        default=f"fk_{relation_name}",
        input_fn=input_fn,
    )
    on_delete = _prompt_action("Politique ON DELETE", default="RESTRICT", input_fn=input_fn)
    on_update = _prompt_action("Politique ON UPDATE", default="CASCADE", input_fn=input_fn)

    return {
        "name": relation_name,
        "type": relation_type,
        "from_entity": from_entity,
        "to_entity": to_entity,
        "from_field": from_field,
        "to_field": to_field,
        "foreign_key_name": foreign_key_name,
        "on_delete": on_delete,
        "on_update": on_update,
    }


def _relation_summary(relation: dict[str, str], entity_map: dict[str, dict[str, Any]]) -> str:
    from_field = next(field for field in entity_map[relation["from_entity"]]["fields"] if field["name"] == relation["from_field"])
    to_field = next(field for field in entity_map[relation["to_entity"]]["fields"] if field["name"] == relation["to_field"])
    return "\n".join(
        [
            f"Type : {relation['type']}",
            f"Relation : {relation['name']}",
            f"Source : {relation['from_entity']}.{relation['from_field']} ({from_field['column']})",
            f"Cible : {relation['to_entity']}.{relation['to_field']} ({to_field['column']})",
            f"Contrainte SQL : {relation['foreign_key_name']}",
            f"ON DELETE : {relation['on_delete']}",
            f"ON UPDATE : {relation['on_update']}",
        ]
    )


def _ensure_no_obvious_duplicates(relations: list[dict[str, Any]], relation: dict[str, str], *, source: str) -> None:
    for existing in relations:
        if existing.get("name") == relation["name"]:
            raise ValueError(f"{source}: une relation nommée {relation['name']!r} existe déjà")
        if existing.get("foreign_key_name") == relation["foreign_key_name"]:
            raise ValueError(f"{source}: une contrainte nommée {relation['foreign_key_name']!r} existe déjà")
        if (
            existing.get("type") == relation["type"]
            and existing.get("from_entity") == relation["from_entity"]
            and existing.get("to_entity") == relation["to_entity"]
            and existing.get("from_field") == relation["from_field"]
            and existing.get("to_field") == relation["to_field"]
        ):
            raise ValueError(f"{source}: cette relation existe déjà")


def main(argv: list[str] | None = None) -> None:
    args = list(sys.argv[1:] if argv is None else argv)
    if args and args[0] in {"-h", "--help"}:
        print(__doc__.strip())
        raise SystemExit(0)
    if args:
        print("Usage : forge make:relation")
        raise SystemExit(1)

    try:
        target_entities_dir = entities_dir()
        entity_map = load_entity_definitions(target_entities_dir)
    except EntityDefinitionError as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)

    if not entity_map:
        print("[ERREUR] Aucune entité disponible. Créez d'abord vos entités avec forge make:entity.")
        raise SystemExit(1)

    relations_path = target_entities_dir / "relations.json"
    try:
        document = _load_relations_document(relations_path)
        relation = _build_relation_interactively(entity_map)
        _ensure_no_obvious_duplicates(document["relations"], relation, source=relations_path.as_posix())
        candidate = {
            "format_version": document["format_version"],
            "relations": [*document["relations"], relation],
        }
        validate_relations_definition(candidate, source=str(relations_path), entities_root=target_entities_dir)
    except (ValueError, EntityRelationsError) as exc:
        print(f"[ERREUR] {exc}")
        raise SystemExit(1)

    print("Résumé avant écriture")
    print(_relation_summary(relation, entity_map))
    print("")
    print("Objet relation ajouté :")
    print(json.dumps(relation, indent=2, ensure_ascii=True))
    print("")
    if not _prompt_yes_no("Confirmer l'écriture de mvc/entities/relations.json ?", default=True):
        print("Aucune écriture effectuée.")
        raise SystemExit(0)

    relations_path.parent.mkdir(parents=True, exist_ok=True)
    relations_path.write_text(json.dumps(candidate, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")

    print("[OK] Relation ajoutée dans mvc/entities/relations.json")
    print("[INFO] Lancez ensuite forge sync:relations pour régénérer mvc/entities/relations.sql.")
    print("[INFO] En V1, un many_to_many se modélise via une entité pivot explicite et deux many_to_one.")


if __name__ == "__main__":
    main()
