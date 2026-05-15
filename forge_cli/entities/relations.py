"""Validation et generation des relations globales Forge."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from forge_cli.entities.validation import EntityDefinitionError, validate_entity_definition


ALLOWED_RELATION_TYPES = {"many_to_one", "many_to_many"}
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
M2M_REQUIRED_KEYS = {
    "type",
    "source",
    "target",
    "pivot_table",
    "source_key",
    "target_key",
}
M2M_OPTIONAL_KEYS = {"pivot_fields", "order_column"}
M2M_KEYS = M2M_REQUIRED_KEYS | M2M_OPTIONAL_KEYS


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


@dataclass(frozen=True)
class ValidatedManyToManyRelation:
    relation_type: str
    source: str
    target: str
    pivot_table: str
    source_key: str
    target_key: str
    pivot_fields: tuple["ValidatedPivotField", ...] = ()
    order_column: str | None = None


@dataclass(frozen=True)
class ValidatedPivotField:
    name: str
    sql_type: str
    nullable: bool


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


def _normalize_sql_type_for_fk(sql_type: str) -> str:
    normalized = sql_type.strip().upper()
    normalized = re.sub(r"\s+", " ", normalized)
    normalized = re.sub(r"\s*\(\s*", "(", normalized)
    normalized = re.sub(r"\s*,\s*", ",", normalized)
    normalized = re.sub(r"\s*\)", ")", normalized)
    return normalized


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
) -> list[ValidatedRelation | ValidatedManyToManyRelation]:
    issues: list[RelationIssue] = []
    entity_map = _safe_load_entities(entities_root, issues)
    _validate_relations_root(data, issues)

    validated_relations: list[ValidatedRelation | ValidatedManyToManyRelation] = []
    if isinstance(data, dict) and isinstance(data.get("relations"), list):
        seen_names: dict[str, int] = {}
        seen_fk_names: dict[str, int] = {}
        seen_pivot_tables: dict[str, tuple[int, tuple]] = {}
        for index, relation in enumerate(data["relations"]):
            if not isinstance(relation, dict):
                continue
            rel_type = relation.get("type") if isinstance(relation.get("type"), str) else None
            if rel_type == "many_to_many":
                validated = _validate_many_to_many_item(relation, index, issues)
                if validated is not None:
                    _validate_unique_pivot_table(
                        validated,
                        index,
                        seen_pivot_tables,
                        issues,
                    )
            else:
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


def generate_relations_sql(relations: list[ValidatedRelation | ValidatedManyToManyRelation]) -> str:
    blocks = []
    for relation in relations:
        if isinstance(relation, ValidatedRelation):
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
        else:
            blocks.append(_generate_many_to_many_sql(relation))
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"


def _generate_many_to_many_sql(relation: ValidatedManyToManyRelation) -> str:
    field_lines = [
        f"    {relation.source_key} INT NOT NULL,",
        f"    {relation.target_key} INT NOT NULL,",
    ]
    for field in relation.pivot_fields:
        null_sql = "NULL" if field.nullable else "NOT NULL"
        field_lines.append(f"    {field.name} {field.sql_type} {null_sql},")
    return "\n".join(
        [
            f"CREATE TABLE IF NOT EXISTS {relation.pivot_table} (",
            *field_lines,
            f"    PRIMARY KEY ({relation.source_key}, {relation.target_key}),",
            f"    INDEX idx_{relation.pivot_table}_{relation.source_key} ({relation.source_key}),",
            f"    INDEX idx_{relation.pivot_table}_{relation.target_key} ({relation.target_key}),",
            f"    CONSTRAINT fk_{relation.pivot_table}_{relation.source_key}",
            f"        FOREIGN KEY ({relation.source_key})",
            f"        REFERENCES {relation.source}(id)",
            "        ON DELETE CASCADE,",
            f"    CONSTRAINT fk_{relation.pivot_table}_{relation.target_key}",
            f"        FOREIGN KEY ({relation.target_key})",
            f"        REFERENCES {relation.target}(id)",
            "        ON DELETE CASCADE",
            ");",
        ]
    )


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
        _add_issue(issues, f"{path}.type", f"type de relation non reconnu : '{relation_type}'")

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

    if _normalize_sql_type_for_fk(from_field.sql_type) != _normalize_sql_type_for_fk(to_field.sql_type):
        _add_issue(
            issues,
            path,
            "from_field et to_field doivent avoir des types SQL identiques pour une cle etrangere MariaDB",
        )

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


def _validate_many_to_many_item(
    relation: dict[str, Any],
    index: int,
    issues: list[RelationIssue],
) -> ValidatedManyToManyRelation | None:
    path = f"relations[{index}]"

    for key in M2M_REQUIRED_KEYS:
        if key not in relation:
            _add_issue(issues, f"{path}.{key}", "cle obligatoire manquante")

    for key, value in relation.items():
        if key not in M2M_KEYS:
            _add_issue(issues, f"{path}.{key}", "cle non supportee pour many_to_many")
        elif key in M2M_REQUIRED_KEYS and not isinstance(value, str):
            _add_issue(issues, f"{path}.{key}", "doit etre une chaine")

    if any(key not in relation or not isinstance(relation[key], str) for key in M2M_REQUIRED_KEYS):
        return None

    source = relation["source"]
    target = relation["target"]
    pivot_table = relation["pivot_table"]
    source_key = relation["source_key"]
    target_key = relation["target_key"]

    for key, value in [
        ("source", source),
        ("target", target),
        ("pivot_table", pivot_table),
        ("source_key", source_key),
        ("target_key", target_key),
    ]:
        if not _is_sql_identifier(value):
            _add_issue(issues, f"{path}.{key}", "doit etre un identifiant SQL valide")

    pivot_fields = _validate_pivot_fields(
        relation.get("pivot_fields"),
        "pivot_fields" in relation,
        path,
        source_key,
        target_key,
        issues,
    )

    order_column = _validate_order_column(
        relation.get("order_column"),
        "order_column" in relation,
        path,
        pivot_fields,
        issues,
    )

    return ValidatedManyToManyRelation(
        relation_type="many_to_many",
        source=source,
        target=target,
        pivot_table=pivot_table,
        source_key=source_key,
        target_key=target_key,
        pivot_fields=tuple(pivot_fields),
        order_column=order_column,
    )


def _validate_pivot_fields(
    value: Any,
    provided: bool,
    relation_path: str,
    source_key: str,
    target_key: str,
    issues: list[RelationIssue],
) -> list[ValidatedPivotField]:
    if not provided:
        return []
    path = f"{relation_path}.pivot_fields"
    if not isinstance(value, list):
        _add_issue(issues, path, "doit etre une liste")
        return []

    fields: list[ValidatedPivotField] = []
    for index, field in enumerate(value):
        field_path = f"{path}[{index}]"
        if not isinstance(field, dict):
            _add_issue(issues, field_path, "doit etre un objet")
            continue

        name = field.get("name")
        sql_type = field.get("sql_type")
        nullable = field.get("nullable", False)

        if "name" not in field:
            _add_issue(issues, f"{field_path}.name", "cle obligatoire manquante")
        elif not isinstance(name, str) or not name.strip():
            _add_issue(issues, f"{field_path}.name", "doit etre une chaine non vide")
        elif not _is_sql_identifier(name):
            _add_issue(issues, f"{field_path}.name", "doit etre un identifiant SQL valide")
        elif name in {source_key, target_key}:
            _add_issue(issues, f"{field_path}.name", "ne doit pas dupliquer source_key ou target_key")

        if "sql_type" not in field:
            _add_issue(issues, f"{field_path}.sql_type", "cle obligatoire manquante")
        elif not isinstance(sql_type, str) or not sql_type.strip():
            _add_issue(issues, f"{field_path}.sql_type", "doit etre une chaine non vide")
        elif not _is_safe_sql_type(sql_type):
            _add_issue(issues, f"{field_path}.sql_type", "contient des caracteres SQL non supportes")

        if "nullable" in field and not isinstance(nullable, bool):
            _add_issue(issues, f"{field_path}.nullable", "doit etre un booleen")

        if (
            isinstance(name, str)
            and name.strip()
            and _is_sql_identifier(name)
            and name not in {source_key, target_key}
            and isinstance(sql_type, str)
            and sql_type.strip()
            and _is_safe_sql_type(sql_type)
            and isinstance(nullable, bool)
        ):
            fields.append(
                ValidatedPivotField(
                    name=name,
                    sql_type=_normalize_sql_type_for_fk(sql_type),
                    nullable=nullable,
                )
            )
    return fields


def _validate_order_column(
    value: Any,
    provided: bool,
    relation_path: str,
    pivot_fields: list[ValidatedPivotField],
    issues: list[RelationIssue],
) -> str | None:
    if not provided:
        return None
    path = f"{relation_path}.order_column"
    if not isinstance(value, str) or not value.strip():
        _add_issue(issues, path, "doit etre une chaine non vide")
        return None
    if not _is_sql_identifier(value):
        _add_issue(issues, path, "doit etre un identifiant SQL valide")
        return None
    pivot_field_names = {f.name for f in pivot_fields}
    if value not in pivot_field_names:
        _add_issue(issues, path, "doit etre le nom d'un champ declare dans pivot_fields")
        return None
    return value


def _is_safe_sql_type(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\([0-9]+(?:,[0-9]+)?\))?(?:\s+[A-Za-z]+)*", value.strip()))


def _validate_unique_pivot_table(
    relation: ValidatedManyToManyRelation,
    index: int,
    seen_pivot_tables: dict[str, tuple[int, tuple]],
    issues: list[RelationIssue],
) -> None:
    signature = (
        relation.source,
        relation.target,
        relation.pivot_table,
        relation.source_key,
        relation.target_key,
        tuple((field.name, field.sql_type, field.nullable) for field in relation.pivot_fields),
        relation.order_column,
    )
    previous = seen_pivot_tables.get(relation.pivot_table)
    if previous is None:
        seen_pivot_tables[relation.pivot_table] = (index, signature)
        return
    previous_index, previous_signature = previous
    if previous_signature != signature:
        _add_issue(
            issues,
            f"relations[{index}].pivot_table",
            (
                "pivot_table deja utilisee avec une definition incompatible "
                f"(deja utilisee par relations[{previous_index}].pivot_table)"
            ),
        )
