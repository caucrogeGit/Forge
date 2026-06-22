"""Validation et generation des relations globales Forge."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cli.entities.canonical_model_normalizer import (
    CanonicalNormalizationError,
    normalize_canonical_entity_for_model_build,
)
from cli.entities.validation import EntityDefinitionError, validate_entity_definition


ALLOWED_RELATION_TYPES = {"many_to_one", "many_to_many"}
_CANONICAL_ON_DELETE_TO_SQL = {
    "restrict": "RESTRICT",
    "cascade": "CASCADE",
    "set_null": "SET NULL",
    "no_action": "NO ACTION",
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


@dataclass(frozen=True)
class ValidatedCanonicalManyToManyRelation:
    from_entity: str
    from_table: str
    to_entity: str
    to_table: str
    pivot_table: str
    from_key: str
    to_key: str
    on_delete: str
    pivot_fields: tuple[ValidatedPivotField, ...] = ()
    relation_type: str = "many_to_many"



@dataclass(frozen=True)
class ValidatedPivotField:
    name: str
    sql_type: str
    nullable: bool
    unique: bool = False


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
        raw_data = json.loads(json_path.read_text(encoding="utf-8"))
        if isinstance(raw_data, dict) and raw_data.get("schema_version") == "1.0":
            legacy_data = normalize_canonical_entity_for_model_build(raw_data)
            data = validate_entity_definition(legacy_data, source=str(json_path))
        else:
            data = validate_entity_definition(raw_data, source=str(json_path))
        entity_name = data["entity"]
        entity_map[entity_name] = data
    return entity_map


def validate_relations_definition(
    data: Any,
    *,
    source: str,
    entities_root: Path,
) -> list[ValidatedRelation | ValidatedCanonicalManyToManyRelation]:
    issues: list[RelationIssue] = []
    entity_map = _safe_load_entities(entities_root, issues)
    _validate_relations_root(data, issues)

    validated_relations: list[ValidatedRelation | ValidatedCanonicalManyToManyRelation] = []
    if isinstance(data, dict) and isinstance(data.get("relations"), list):
        seen_names: dict[str, int] = {}
        seen_fk_names: dict[str, int] = {}
        seen_pivot_tables: dict[str, tuple[int, tuple]] = {}
        for index, relation in enumerate(data["relations"]):
            if not isinstance(relation, dict):
                continue
            rel_type = relation.get("type") if isinstance(relation.get("type"), str) else None
            if rel_type == "many_to_many":
                if "pivot" in relation:
                    validated = _validate_m2m_canonical(
                        relation,
                        index,
                        entity_map,
                        seen_names,
                        seen_pivot_tables,
                        issues,
                    )
                else:
                    _add_issue(
                        issues,
                        f"relations[{index}]",
                        "format legacy refusé — utilisez un bloc 'pivot' (relation canonique many_to_many)",
                    )
                    validated = None
            elif "from" in relation and "from_entity" not in relation:
                validated = _validate_relation_item_canonical(
                    relation,
                    index,
                    entity_map,
                    seen_names,
                    seen_fk_names,
                    issues,
                )
            else:
                _add_issue(
                    issues,
                    f"relations[{index}]",
                    "format legacy refusé — utilisez 'from', 'to', 'foreign_key' (relation canonique many_to_one)",
                )
                validated = None
            if validated is not None:
                validated_relations.append(validated)

    if issues:
        raise EntityRelationsError(source, issues)
    return validated_relations


def generate_relations_sql(relations: list[ValidatedRelation | ValidatedCanonicalManyToManyRelation]) -> str:
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
        elif isinstance(relation, ValidatedCanonicalManyToManyRelation):
            blocks.append(_generate_canonical_m2m_sql(relation))
    if not blocks:
        return ""
    return "\n\n".join(blocks) + "\n"


def _generate_canonical_m2m_sql(relation: ValidatedCanonicalManyToManyRelation) -> str:
    pivot = relation.pivot_table
    fk = relation.from_key
    tk = relation.to_key
    on_delete = relation.on_delete

    field_lines: list[str] = []
    unique_key_lines: list[str] = []
    for f in relation.pivot_fields:
        null_sql = "NULL" if f.nullable else "NOT NULL"
        field_lines.append(f"    {f.name} {f.sql_type} {null_sql},")
        if f.unique:
            unique_key_lines.append(f"    UNIQUE KEY uq_{pivot}_{f.name} ({f.name}),")

    lines: list[str] = [
        f"CREATE TABLE IF NOT EXISTS {pivot} (",
        "    id INT NOT NULL AUTO_INCREMENT,",
        f"    {fk} INT NOT NULL,",
        f"    {tk} INT NOT NULL,",
        *field_lines,
        "    PRIMARY KEY (id),",
        f"    UNIQUE KEY uq_{pivot} ({fk}, {tk}),",
        *unique_key_lines,
        f"    INDEX idx_{pivot}_{fk} ({fk}),",
        f"    INDEX idx_{pivot}_{tk} ({tk}),",
        f"    CONSTRAINT fk_{pivot}_{fk}",
        f"        FOREIGN KEY ({fk})",
        f"        REFERENCES {relation.from_table} (id)",
        f"        ON DELETE {on_delete},",
        f"    CONSTRAINT fk_{pivot}_{tk}",
        f"        FOREIGN KEY ({tk})",
        f"        REFERENCES {relation.to_table} (id)",
        f"        ON DELETE {on_delete}",
        ");",
    ]
    return "\n".join(lines)


_FORGE_PIVOT_SIMPLE_TYPES: dict[str, str] = {
    "text":        "TEXT",
    "integer":     "INT",
    "big_integer": "BIGINT",
    "float":       "DOUBLE",
    "boolean":     "BOOLEAN",
    "date":        "DATE",
    "datetime":    "DATETIME",
    "email":       "VARCHAR(255)",
    "password":    "VARCHAR(255)",
    "json":        "LONGTEXT",
}

_FORGE_PIVOT_ALL_TYPES = set(_FORGE_PIVOT_SIMPLE_TYPES) | {"string", "decimal"}


def _pivot_field_sql_type(
    forge_type: str,
    field: dict[str, Any],
    field_path: str,
    issues: list[RelationIssue],
) -> str | None:
    if forge_type == "string":
        max_length = field.get("max_length", 255)
        if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length <= 0:
            _add_issue(issues, f"{field_path}.max_length", "doit etre un entier positif pour le type 'string'")
            return None
        return f"VARCHAR({max_length})"
    if forge_type == "decimal":
        precision = field.get("precision")
        scale = field.get("scale")
        if not isinstance(precision, int) or isinstance(precision, bool) or precision <= 0:
            _add_issue(issues, f"{field_path}.precision", "requis et entier positif pour le type 'decimal'")
            return None
        if not isinstance(scale, int) or isinstance(scale, bool) or scale < 0:
            _add_issue(issues, f"{field_path}.scale", "requis et entier >= 0 pour le type 'decimal'")
            return None
        return f"DECIMAL({precision},{scale})"
    return _FORGE_PIVOT_SIMPLE_TYPES.get(forge_type)


def _validate_canonical_pivot_fields(
    fields_raw: Any,
    path: str,
    from_key: str,
    to_key: str,
    issues: list[RelationIssue],
) -> list[ValidatedPivotField]:
    """Validate pivot.fields[] in a canonical many_to_many relation."""
    if not isinstance(fields_raw, list):
        _add_issue(issues, f"{path}.pivot.fields", "doit etre une liste")
        return []

    reserved = {"id", from_key, to_key}
    result: list[ValidatedPivotField] = []

    for i, field in enumerate(fields_raw):
        field_path = f"{path}.pivot.fields[{i}]"
        if not isinstance(field, dict):
            _add_issue(issues, field_path, "doit etre un objet")
            continue

        name = field.get("name")
        forge_type = field.get("type")

        if not isinstance(name, str) or not name:
            _add_issue(issues, f"{field_path}.name", "cle obligatoire manquante ou invalide")
            continue
        if not _is_sql_identifier(name):
            _add_issue(issues, f"{field_path}.name", "doit etre un identifiant SQL valide")
            continue
        if name in reserved:
            _add_issue(
                issues,
                f"{field_path}.name",
                f"nom reserve interdit dans pivot.fields : {name!r} (id, from_key, to_key sont geres par Forge)",
            )
            continue

        if not isinstance(forge_type, str) or forge_type not in _FORGE_PIVOT_ALL_TYPES:
            allowed = ", ".join(sorted(_FORGE_PIVOT_ALL_TYPES))
            _add_issue(
                issues,
                f"{field_path}.type",
                f"type Forge invalide ou manquant. Valeurs supportees : {allowed}",
            )
            continue

        sql_type = _pivot_field_sql_type(forge_type, field, field_path, issues)
        if sql_type is None:
            continue

        nullable = bool(field.get("nullable", True))
        if field.get("required") is True:
            nullable = False

        unique = bool(field.get("unique", False))
        result.append(ValidatedPivotField(name=name, sql_type=sql_type, nullable=nullable, unique=unique))

    return result


def _validate_m2m_canonical(
    relation: dict[str, Any],
    index: int,
    entity_map: dict[str, dict[str, Any]],
    seen_names: dict[str, int],
    seen_pivot_tables: dict[str, tuple[int, tuple]],
    issues: list[RelationIssue],
) -> ValidatedCanonicalManyToManyRelation | None:
    path = f"relations[{index}]"

    for key in ("type", "from", "to", "name", "pivot"):
        if key not in relation:
            _add_issue(issues, f"{path}.{key}", "cle obligatoire manquante (relation canonique many_to_many)")
    if any(key not in relation for key in ("type", "from", "to", "name", "pivot")):
        return None

    for key in ("from", "to", "name"):
        if not isinstance(relation[key], str):
            _add_issue(issues, f"{path}.{key}", "doit etre une chaine")

    relation_name = relation["name"]
    from_entity_name = relation["from"]
    to_entity_name = relation["to"]

    if not _is_sql_identifier(relation_name):
        _add_issue(issues, f"{path}.name", "doit etre un identifiant valide")
    if not _is_pascal_case(from_entity_name):
        _add_issue(issues, f"{path}.from", "doit etre un nom d'entite PascalCase valide")
    if not _is_pascal_case(to_entity_name):
        _add_issue(issues, f"{path}.to", "doit etre un nom d'entite PascalCase valide")

    if relation_name in seen_names:
        _add_issue(
            issues,
            f"{path}.name",
            f"doit etre unique (deja utilise par relations[{seen_names[relation_name]}].name)",
        )
    else:
        seen_names[relation_name] = index

    pivot = relation["pivot"]
    if not isinstance(pivot, dict):
        _add_issue(issues, f"{path}.pivot", "doit etre un objet")
        return None

    for key in ("table", "from_key", "to_key"):
        if key not in pivot:
            _add_issue(issues, f"{path}.pivot.{key}", "cle obligatoire manquante")

    if pivot.get("id") is not True:
        _add_issue(issues, f"{path}.pivot.id", "doit valoir true")
    if pivot.get("unique_pair") is not True:
        _add_issue(issues, f"{path}.pivot.unique_pair", "doit valoir true")

    pivot_table = pivot.get("table", "")
    from_key = pivot.get("from_key", "")
    to_key = pivot.get("to_key", "")

    if not isinstance(pivot_table, str) or not _is_sql_identifier(pivot_table):
        _add_issue(issues, f"{path}.pivot.table", "doit etre un identifiant SQL valide")
        pivot_table = ""
    if not isinstance(from_key, str) or not _is_sql_identifier(from_key):
        _add_issue(issues, f"{path}.pivot.from_key", "doit etre un identifiant SQL valide")
        from_key = ""
    if not isinstance(to_key, str) or not _is_sql_identifier(to_key):
        _add_issue(issues, f"{path}.pivot.to_key", "doit etre un identifiant SQL valide")
        to_key = ""

    if from_key and to_key and from_key == to_key:
        _add_issue(issues, path, "pivot.from_key et pivot.to_key doivent etre differents")

    on_delete_raw = pivot.get("on_delete", "cascade")
    on_delete_sql = _CANONICAL_ON_DELETE_TO_SQL.get(on_delete_raw if isinstance(on_delete_raw, str) else "")
    if on_delete_sql is None:
        _add_issue(
            issues,
            f"{path}.pivot.on_delete",
            f"valeur invalide : {on_delete_raw!r}. Valeurs attendues : {', '.join(sorted(_CANONICAL_ON_DELETE_TO_SQL))}",
        )

    if pivot_table:
        if pivot_table in seen_pivot_tables:
            prev_index, _ = seen_pivot_tables[pivot_table]
            _add_issue(
                issues,
                f"{path}.pivot.table",
                f"table pivot deja utilisee par relations[{prev_index}]",
            )
        else:
            seen_pivot_tables[pivot_table] = (index, (pivot_table,))

    from_entity = entity_map.get(from_entity_name)
    if from_entity is None:
        _add_issue(issues, path, f"l'entite {from_entity_name!r} est introuvable")
    to_entity = entity_map.get(to_entity_name)
    if to_entity is None:
        _add_issue(issues, path, f"l'entite {to_entity_name!r} est introuvable")

    if from_entity is None or to_entity is None or on_delete_sql is None:
        return None
    if not pivot_table or not from_key or not to_key or from_key == to_key:
        return None

    fields_raw = pivot.get("fields", [])
    pivot_fields = _validate_canonical_pivot_fields(
        fields_raw,
        f"relations[{index}]",
        from_key,
        to_key,
        issues,
    )

    return ValidatedCanonicalManyToManyRelation(
        from_entity=from_entity_name,
        from_table=from_entity["table"],
        to_entity=to_entity_name,
        to_table=to_entity["table"],
        pivot_table=pivot_table,
        from_key=from_key,
        to_key=to_key,
        on_delete=on_delete_sql,
        pivot_fields=tuple(pivot_fields),
    )



def _safe_load_entities(entities_root: Path, issues: list[RelationIssue]) -> dict[str, dict[str, Any]]:
    try:
        return load_entity_definitions(entities_root)
    except (EntityDefinitionError, CanonicalNormalizationError) as exc:
        _add_issue(issues, "entities", str(exc))
        return {}


def _validate_relations_root(data: Any, issues: list[RelationIssue]) -> None:
    if not isinstance(data, dict):
        _add_issue(issues, "$", "la racine doit etre un objet JSON")
        return

    if "format_version" in data:
        _add_issue(
            issues,
            "format_version",
            'Le format format_version: 1 n\'est plus accepté pour relations.json. '
            'Utilisez schema_version: "1.0".',
        )
        return

    if data.get("schema_version") != "1.0":
        _add_issue(issues, "schema_version", 'doit valoir "1.0"')

    if "relations" not in data:
        _add_issue(issues, "relations", "cle obligatoire manquante")

    if "relations" in data:
        if not isinstance(data["relations"], list):
            _add_issue(issues, "relations", "doit etre une liste")
        else:
            for index, relation in enumerate(data["relations"]):
                if not isinstance(relation, dict):
                    _add_issue(issues, f"relations[{index}]", "doit etre un objet")


def _validate_relation_item_canonical(
    relation: dict[str, Any],
    index: int,
    entity_map: dict[str, dict[str, Any]],
    seen_names: dict[str, int],
    seen_fk_names: dict[str, int],
    issues: list[RelationIssue],
) -> ValidatedRelation | None:
    """Validate a canonical many_to_one relation (schema_version 1.0) and produce a ValidatedRelation."""
    path = f"relations[{index}]"

    required_keys = {"type", "from", "to", "name", "foreign_key", "on_delete"}
    for key in required_keys:
        if key not in relation:
            _add_issue(issues, f"{path}.{key}", "cle obligatoire manquante (relation canonique)")
    if any(key not in relation for key in required_keys):
        return None

    for key in required_keys:
        if not isinstance(relation[key], str):
            _add_issue(issues, f"{path}.{key}", "doit etre une chaine")

    relation_name = relation["name"]
    from_entity_name = relation["from"]
    to_entity_name = relation["to"]
    foreign_key = relation["foreign_key"]
    on_delete_raw = relation["on_delete"]

    if not _is_sql_identifier(relation_name):
        _add_issue(issues, f"{path}.name", "doit etre un identifiant valide")
    if not _is_pascal_case(from_entity_name):
        _add_issue(issues, f"{path}.from", "doit etre un nom d'entite PascalCase valide")
    if not _is_pascal_case(to_entity_name):
        _add_issue(issues, f"{path}.to", "doit etre un nom d'entite PascalCase valide")
    if not _is_sql_identifier(foreign_key):
        _add_issue(issues, f"{path}.foreign_key", "doit etre un identifiant SQL valide")

    on_delete_sql = _CANONICAL_ON_DELETE_TO_SQL.get(on_delete_raw if isinstance(on_delete_raw, str) else "")
    if on_delete_sql is None:
        _add_issue(
            issues,
            f"{path}.on_delete",
            f"valeur invalide : {on_delete_raw!r}. Valeurs attendues : {', '.join(sorted(_CANONICAL_ON_DELETE_TO_SQL))}",
        )

    if relation_name in seen_names:
        _add_issue(
            issues,
            f"{path}.name",
            f"doit etre unique (deja utilise par relations[{seen_names[relation_name]}].name)",
        )
    else:
        seen_names[relation_name] = index

    if foreign_key in seen_fk_names:
        _add_issue(
            issues,
            f"{path}.foreign_key",
            f"doit etre unique (deja utilise par relations[{seen_fk_names[foreign_key]}].foreign_key)",
        )
    else:
        seen_fk_names[foreign_key] = index

    from_entity = entity_map.get(from_entity_name)
    if from_entity is None:
        _add_issue(issues, path, f"l'entite {from_entity_name!r} est introuvable")
    to_entity = entity_map.get(to_entity_name)
    if to_entity is None:
        _add_issue(issues, path, f"l'entite {to_entity_name!r} est introuvable")

    if from_entity is None or to_entity is None or on_delete_sql is None:
        return None

    from_table = from_entity["table"]
    to_table = to_entity["table"]

    to_pk = next((f for f in to_entity["fields"] if f.get("primary_key")), None)
    if to_pk is None:
        _add_issue(issues, path, f"l'entite cible {to_entity_name!r} n'a pas de cle primaire")
        return None

    to_field_name = to_pk["name"]
    to_column = to_pk["column"]
    to_python_type = to_pk["python_type"]

    from_field_match = next(
        (f for f in from_entity["fields"] if f.get("column") == foreign_key or f.get("name") == foreign_key),
        None,
    )
    if from_field_match is not None:
        from_field_name = from_field_match["name"]
        from_python_type = from_field_match["python_type"]
        if from_python_type != to_python_type:
            _add_issue(issues, path, "from et to doivent avoir des types Python compatibles")
        if on_delete_sql == "SET NULL" and not from_field_match.get("nullable", False):
            _add_issue(issues, f"{path}.on_delete", "SET NULL requiert un from_field nullable")
    else:
        from_field_name = foreign_key
        from_python_type = to_python_type

    constraint_name = f"fk_{from_table}_{foreign_key}"

    return ValidatedRelation(
        name=relation_name,
        relation_type="many_to_one",
        foreign_key_name=constraint_name,
        from_entity=from_entity_name,
        from_table=from_table,
        from_field=from_field_name,
        from_column=foreign_key,
        from_python_type=from_python_type,
        to_entity=to_entity_name,
        to_table=to_table,
        to_field=to_field_name,
        to_column=to_column,
        to_python_type=to_python_type,
        on_delete=on_delete_sql,
        on_update="RESTRICT",
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


def _is_safe_sql_type(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*(?:\([0-9]+(?:,[0-9]+)?\))?(?:\s+[A-Za-z]+)*", value.strip()))
