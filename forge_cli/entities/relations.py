"""Validation et generation des relations globales Forge."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge_cli.entities.validation import EntityDefinitionError, validate_entity_definition


ALLOWED_RELATION_TYPES = {"many_to_one"}
ALLOWED_ACTIONS = {"RESTRICT", "CASCADE", "SET NULL", "NO ACTION"}
RELATION_KEYS = {
    "name",
    "type",
    "from_entity",
    "to_entity",
    "from_field",
    "to_field",
    "foreign_key_name",
    "on_delete",
    "on_update",
}


@dataclass(frozen=True)
class ResolvedEntityField:
    entity_name: str
    table_name: str
    field_name: str
    column_name: str
    python_type: str
    sql_type: str
    nullable: bool
    primary_key: bool


@dataclass(frozen=True)
class ValidatedRelation:
    name: str
    relation_type: str
    foreign_key_name: str
    from_entity: str
    from_table: str
    from_field: str
    from_column: str
    from_python_type: str
    to_entity: str
    to_table: str
    to_field: str
    to_column: str
    to_python_type: str
    on_delete: str
    on_update: str


@dataclass
class RelationIssue:
    path: str
    message: str


class EntityRelationsError(ValueError):
    """Erreur de definition des relations globales."""

    def __init__(self, source: str, issues: list[RelationIssue]):
        self.source = source
        self.issues = issues
        lines = [f"{source}: JSON de relations invalide ({len(issues)} erreur(s))"]
        for issue in issues:
            lines.append(f"- {issue.path}: {issue.message}")
        super().__init__("\n".join(lines))


def _add_issue(issues: list[RelationIssue], path: str, message: str) -> None:
    issues.append(RelationIssue(path=path, message=message))


def _is_sql_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value))


def _is_pascal_case(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", value))


def load_entity_definitions(entities_root: Path) -> dict[str, dict[str, Any]]:
    entity_map: dict[str, dict[str, Any]] = {}
    for json_path in sorted(entities_root.glob("*/*.json")):
        if json_path.name == "relations.json":
            continue
        data = validate_entity_definition(
            json.loads(json_path.read_text(encoding="utf-8")),
            source=str(json_path),
        )
        entity_name = data["entity"]
        entity_map[entity_name] = data
    return entity_map


def validate_relations_definition(
    data: Any,
    *,
    source: str,
    entities_root: Path,
) -> list[ValidatedRelation]:
    issues: list[RelationIssue] = []
    entity_map = _safe_load_entities(entities_root, issues)
    _validate_relations_root(data, issues)

    validated_relations: list[ValidatedRelation] = []
    if isinstance(data, dict) and isinstance(data.get("relations"), list):
        seen_names: dict[str, int] = {}
        seen_fk_names: dict[str, int] = {}
        for index, relation in enumerate(data["relations"]):
            validated = _validate_relation_item(
                relation,
                index,
                entity_map,
                seen_names,
                seen_fk_names,
                issues,
            )
            if validated is not None:
                validated_relations.append(validated)

    if issues:
        raise EntityRelationsError(source, issues)
    return validated_relations


def generate_relations_sql(relations: list[ValidatedRelation]) -> str:
    blocks = []
    for relation in relations:
        blocks.append(
            "\n".join(
                [
                    f"ALTER TABLE {relation.from_table}",
                    f"    ADD CONSTRAINT {relation.foreign_key_name}",
                    f"    FOREIGN KEY ({relation.from_column})",
                    f"    REFERENCES {relation.to_table} ({relation.to_column})",
                    f"    ON DELETE {relation.on_delete}",
                    f"    ON UPDATE {relation.on_update};",
                ]
            )
        )
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"


def _safe_load_entities(entities_root: Path, issues: list[RelationIssue]) -> dict[str, dict[str, Any]]:
    try:
        return load_entity_definitions(entities_root)
    except EntityDefinitionError as exc:
        _add_issue(issues, "entities", str(exc))
        return {}


def _validate_relations_root(data: Any, issues: list[RelationIssue]) -> None:
    if not isinstance(data, dict):
        _add_issue(issues, "$", "la racine doit etre un objet JSON")
        return

    for key in ("format_version", "relations"):
        if key not in data:
            _add_issue(issues, key, "cle obligatoire manquante")

    if "format_version" in data:
        if not isinstance(data["format_version"], int) or isinstance(data["format_version"], bool):
            _add_issue(issues, "format_version", "doit etre un entier")
        elif data["format_version"] != 1:
            _add_issue(issues, "format_version", "doit valoir 1 en V1")

    if "relations" in data:
        if not isinstance(data["relations"], list):
            _add_issue(issues, "relations", "doit etre une liste")
        else:
            for index, relation in enumerate(data["relations"]):
                if not isinstance(relation, dict):
                    _add_issue(issues, f"relations[{index}]", "doit etre un objet")


def _validate_relation_item(
    relation: Any,
    index: int,
    entity_map: dict[str, dict[str, Any]],
    seen_names: dict[str, int],
    seen_fk_names: dict[str, int],
    issues: list[RelationIssue],
) -> ValidatedRelation | None:
    path = f"relations[{index}]"
    if not isinstance(relation, dict):
        return None

    for key in RELATION_KEYS:
        if key not in relation:
            _add_issue(issues, f"{path}.{key}", "cle obligatoire manquante")

    for key, value in relation.items():
        if key not in RELATION_KEYS:
            _add_issue(issues, f"{path}.{key}", "cle non supportee en V1")
        elif not isinstance(value, str):
            _add_issue(issues, f"{path}.{key}", "doit etre une chaine")

    if any(key not in relation or not isinstance(relation[key], str) for key in RELATION_KEYS):
        return None

    relation_name = relation["name"]
    relation_type = relation["type"]
    from_entity_name = relation["from_entity"]
    to_entity_name = relation["to_entity"]
    from_field_name = relation["from_field"]
    to_field_name = relation["to_field"]
    foreign_key_name = relation["foreign_key_name"]
    on_delete = relation["on_delete"].upper()
    on_update = relation["on_update"].upper()

    if not _is_sql_identifier(relation_name):
        _add_issue(issues, f"{path}.name", "doit etre un identifiant valide")
    if not _is_pascal_case(from_entity_name):
        _add_issue(issues, f"{path}.from_entity", "doit etre un nom d'entite PascalCase valide")
    if not _is_pascal_case(to_entity_name):
        _add_issue(issues, f"{path}.to_entity", "doit etre un nom d'entite PascalCase valide")
    if not _is_sql_identifier(foreign_key_name):
        _add_issue(issues, f"{path}.foreign_key_name", "doit etre un identifiant SQL valide")

    if relation_name in seen_names:
        _add_issue(
            issues,
            f"{path}.name",
            f"doit etre unique (deja utilise par relations[{seen_names[relation_name]}].name)",
        )
    else:
        seen_names[relation_name] = index

    if foreign_key_name in seen_fk_names:
        _add_issue(
            issues,
            f"{path}.foreign_key_name",
            f"doit etre unique (deja utilise par relations[{seen_fk_names[foreign_key_name]}].foreign_key_name)",
        )
    else:
        seen_fk_names[foreign_key_name] = index

    if relation_type not in ALLOWED_RELATION_TYPES:
        _add_issue(issues, f"{path}.type", "doit valoir 'many_to_one' en V1")

    if on_delete not in ALLOWED_ACTIONS:
        _add_issue(issues, f"{path}.on_delete", "doit etre l'une des valeurs SQL supportees en V1")
    if on_update not in ALLOWED_ACTIONS:
        _add_issue(issues, f"{path}.on_update", "doit etre l'une des valeurs SQL supportees en V1")

    from_field = _resolve_entity_field(entity_map, from_entity_name, from_field_name, f"{path}.from_field", issues)
    to_field = _resolve_entity_field(entity_map, to_entity_name, to_field_name, f"{path}.to_field", issues)

    if from_field is None or to_field is None:
        return None

    if not to_field.primary_key:
        _add_issue(issues, f"{path}.to_field", "doit cibler la cle primaire de l'entite cible")

    if from_field.python_type != to_field.python_type:
        _add_issue(issues, path, "from_field et to_field doivent avoir des types Python compatibles")

    if on_delete == "SET NULL" and not from_field.nullable:
        _add_issue(issues, f"{path}.on_delete", "SET NULL requiert un from_field nullable")

    return ValidatedRelation(
        name=relation_name,
        relation_type=relation_type,
        foreign_key_name=foreign_key_name,
        from_entity=from_entity_name,
        from_table=from_field.table_name,
        from_field=from_field_name,
        from_column=from_field.column_name,
        from_python_type=from_field.python_type,
        to_entity=to_entity_name,
        to_table=to_field.table_name,
        to_field=to_field_name,
        to_column=to_field.column_name,
        to_python_type=to_field.python_type,
        on_delete=on_delete,
        on_update=on_update,
    )


def _resolve_entity_field(
    entity_map: dict[str, dict[str, Any]],
    entity_name: str,
    field_name: str,
    issue_path: str,
    issues: list[RelationIssue],
) -> ResolvedEntityField | None:
    entity = entity_map.get(entity_name)
    if entity is None:
        _add_issue(issues, issue_path.rsplit(".", 1)[0], f"l'entite {entity_name!r} est introuvable")
        return None

    for field in entity["fields"]:
        if field["name"] == field_name:
            return ResolvedEntityField(
                entity_name=entity_name,
                table_name=entity["table"],
                field_name=field_name,
                column_name=field["column"],
                python_type=field["python_type"],
                sql_type=field["sql_type"],
                nullable=field["nullable"],
                primary_key=field["primary_key"],
            )

    _add_issue(issues, issue_path, f"le champ {field_name!r} est introuvable dans l'entite {entity_name!r}")
    return None
