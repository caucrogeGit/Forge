"""Validation canonique des JSON d'entite Forge."""

from __future__ import annotations

import re
from datetime import date, datetime
from dataclasses import dataclass
from typing import Any


# Choix V1 explicite : types Python supportes par la source canonique.
ALLOWED_PYTHON_TYPES = {"int", "str", "float", "bool", "date", "datetime"}
ALLOWED_FIELD_KEYS = {
    "name",
    "column",
    "python_type",
    "sql_type",
    "nullable",
    "primary_key",
    "auto_increment",
    "constraints",
    "default",
    "unique",
}
ALLOWED_CONSTRAINT_KEYS = {
    "not_empty",
    "min_length",
    "max_length",
    "min_value",
    "max_value",
    "pattern",
}
INTEGER_SQL_PREFIXES = ("INT", "BIGINT", "SMALLINT", "TINYINT", "MEDIUMINT")
FLOAT_SQL_PREFIXES = ("FLOAT", "DOUBLE", "REAL", "DECIMAL", "NUMERIC")
STRING_SQL_PREFIXES = ("CHAR", "VARCHAR", "TEXT", "TINYTEXT", "MEDIUMTEXT", "LONGTEXT")
SQL_RESERVED_WORDS = {
    "add",
    "alter",
    "and",
    "by",
    "create",
    "delete",
    "drop",
    "from",
    "group",
    "index",
    "insert",
    "into",
    "join",
    "key",
    "order",
    "primary",
    "references",
    "select",
    "table",
    "update",
    "user",
    "where",
}


@dataclass
class EntityDefinitionIssue:
    path: str
    message: str


class EntityDefinitionError(ValueError):
    """Erreur de definition canonique d'une entite."""

    def __init__(self, source: str, issues: list[EntityDefinitionIssue]):
        self.source = source
        self.issues = issues
        lines = [f"{source}: JSON d'entite invalide ({len(issues)} erreur(s))"]
        for issue in issues:
            lines.append(f"- {issue.path}: {issue.message}")
        super().__init__("\n".join(lines))


def _is_bool(value: Any) -> bool:
    return isinstance(value, bool)


def _is_int_but_not_bool(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number_but_not_bool(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_pascal_case(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Z][A-Za-z0-9]*", value))


def _is_snake_case(value: str) -> bool:
    return bool(re.fullmatch(r"[a-z][a-z0-9_]*", value))


def _is_sql_identifier(value: str) -> bool:
    return bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", value))


def _is_sql_reserved_word(value: str) -> bool:
    return value.lower() in SQL_RESERVED_WORDS


def _normalize_sql_type(sql_type: str) -> str:
    return sql_type.strip().upper()


def _to_snake(name: str) -> str:
    value = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    value = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", value)
    return value.replace("-", "_").lower()


def _column_from_field_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def _sql_family(sql_type: str) -> str | None:
    normalized = _normalize_sql_type(sql_type)
    if normalized == "DATE":
        return "date"
    if normalized in {"DATETIME", "TIMESTAMP"}:
        return "datetime"
    for prefix in INTEGER_SQL_PREFIXES:
        if normalized.startswith(prefix):
            return "int"
    for prefix in FLOAT_SQL_PREFIXES:
        if normalized.startswith(prefix):
            return "float"
    for prefix in STRING_SQL_PREFIXES:
        if normalized.startswith(prefix):
            return "str"
    if normalized in {"BOOL", "BOOLEAN"}:
        return "bool"
    return None


def _python_sql_compatible(python_type: str, sql_type: str) -> bool:
    family = _sql_family(sql_type)
    return family == python_type


def _is_iso_date_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        date.fromisoformat(value)
    except ValueError:
        return False
    return True


def _is_iso_datetime_string(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        datetime.fromisoformat(value)
    except ValueError:
        return False
    return True


def normalize_entity_definition(data: Any, *, source: str = "<entity.json>") -> dict[str, Any]:
    issues: list[EntityDefinitionIssue] = []
    _validate_root_structure(data, issues)
    normalized = _normalize_entity_data(data, issues)
    if normalized is not None:
        _validate_entity_local_consistency(normalized, issues)

    if issues:
        raise EntityDefinitionError(source, issues)
    assert normalized is not None
    return normalized


def validate_entity_definition(data: Any, *, source: str = "<entity.json>") -> dict[str, Any]:
    return normalize_entity_definition(data, source=source)


def _add_issue(issues: list[EntityDefinitionIssue], path: str, message: str) -> None:
    issues.append(EntityDefinitionIssue(path=path, message=message))


def _validate_root_structure(data: Any, issues: list[EntityDefinitionIssue]) -> None:
    if not isinstance(data, dict):
        _add_issue(issues, "$", "la racine doit etre un objet JSON")
        return

    required_root_keys = ["entity", "fields"]
    for key in required_root_keys:
        if key not in data:
            _add_issue(issues, key, "cle obligatoire manquante")

    if "format_version" in data and not _is_int_but_not_bool(data["format_version"]):
        _add_issue(issues, "format_version", "doit etre un entier")

    if "entity" in data and not isinstance(data["entity"], str):
        _add_issue(issues, "entity", "doit etre une chaine")

    if "table" in data and not isinstance(data["table"], str):
        _add_issue(issues, "table", "doit etre une chaine")

    if "description" in data and not isinstance(data["description"], str):
        _add_issue(issues, "description", "doit etre une chaine")

    if "fields" in data:
        if not isinstance(data["fields"], list):
            _add_issue(issues, "fields", "doit etre une liste")
        elif not data["fields"]:
            _add_issue(issues, "fields", "doit contenir au moins un champ")
        else:
            for index, field in enumerate(data["fields"]):
                _validate_field_structure(field, index, issues)


def _validate_field_structure(field: Any, index: int, issues: list[EntityDefinitionIssue]) -> None:
    path = f"fields[{index}]"
    if not isinstance(field, dict):
        _add_issue(issues, path, "doit etre un objet")
        return

    required_keys = ["name", "sql_type"]
    for key in required_keys:
        if key not in field:
            _add_issue(issues, f"{path}.{key}", "cle obligatoire manquante")

    for key in field:
        if key not in ALLOWED_FIELD_KEYS:
            _add_issue(issues, f"{path}.{key}", "cle non supportee en V1")

    if "name" in field and not isinstance(field["name"], str):
        _add_issue(issues, f"{path}.name", "doit etre une chaine")
    if "column" in field and not isinstance(field["column"], str):
        _add_issue(issues, f"{path}.column", "doit etre une chaine")
    if "python_type" in field and not isinstance(field["python_type"], str):
        _add_issue(issues, f"{path}.python_type", "doit etre une chaine")
    if "sql_type" in field and not isinstance(field["sql_type"], str):
        _add_issue(issues, f"{path}.sql_type", "doit etre une chaine")
    if "nullable" in field and not isinstance(field["nullable"], bool):
        _add_issue(issues, f"{path}.nullable", "doit etre un booleen")
    if "primary_key" in field and not isinstance(field["primary_key"], bool):
        _add_issue(issues, f"{path}.primary_key", "doit etre un booleen")
    if "auto_increment" in field and not isinstance(field["auto_increment"], bool):
        _add_issue(issues, f"{path}.auto_increment", "doit etre un booleen")
    if "unique" in field and not isinstance(field["unique"], bool):
        _add_issue(issues, f"{path}.unique", "doit etre un booleen")

    constraints = field.get("constraints")
    if "constraints" in field and not isinstance(constraints, dict):
        _add_issue(issues, f"{path}.constraints", "doit etre un objet")
    elif isinstance(constraints, dict):
        for key in constraints:
            if key not in ALLOWED_CONSTRAINT_KEYS:
                _add_issue(issues, f"{path}.constraints.{key}", "contrainte non supportee en V1")


def _normalize_entity_data(
    data: Any,
    issues: list[EntityDefinitionIssue],
) -> dict[str, Any] | None:
    if not isinstance(data, dict):
        return None

    fields = data.get("fields")
    if not isinstance(fields, list):
        return None

    entity = data.get("entity")
    table = data.get("table")
    normalized = {
        "format_version": data.get("format_version", 1),
        "entity": entity,
        "table": table if "table" in data else (_to_snake(entity) if isinstance(entity, str) else ""),
        "description": data.get("description", ""),
        "fields": [],
    }

    for index, field in enumerate(fields):
        normalized_field = _normalize_field_data(field, index, issues)
        if normalized_field is not None:
            normalized["fields"].append(normalized_field)

    return normalized


def _normalize_field_data(
    field: Any,
    index: int,
    issues: list[EntityDefinitionIssue],
) -> dict[str, Any] | None:
    path = f"fields[{index}]"
    if not isinstance(field, dict):
        return None

    name = field.get("name")
    sql_type = field.get("sql_type")
    python_type = field.get("python_type")
    if "python_type" not in field and isinstance(sql_type, str):
        python_type = _sql_family(sql_type)
        if python_type is None:
            _add_issue(
                issues,
                f"{path}.python_type",
                "absent et impossible a deduire depuis sql_type",
            )

    constraints = field.get("constraints", {})
    if not isinstance(constraints, dict):
        constraints = {}

    normalized_field = {
        "name": name,
        "column": field.get("column", _column_from_field_name(name) if isinstance(name, str) else ""),
        "python_type": python_type,
        "sql_type": sql_type,
        "nullable": field.get("nullable", False),
        "primary_key": field.get("primary_key", False),
        "auto_increment": field.get("auto_increment", False),
        "constraints": dict(constraints),
        "unique": field.get("unique", False),
    }
    if "default" in field:
        normalized_field["default"] = field["default"]
    return normalized_field


def _validate_entity_local_consistency(data: dict[str, Any], issues: list[EntityDefinitionIssue]) -> None:
    if isinstance(data.get("format_version"), int) and data["format_version"] != 1:
        _add_issue(issues, "format_version", "doit valoir 1 en V1")

    entity = data.get("entity")
    if isinstance(entity, str) and not _is_pascal_case(entity):
        _add_issue(issues, "entity", "doit etre un nom PascalCase valide")
    elif isinstance(entity, str) and _is_sql_reserved_word(entity):
        _add_issue(issues, "entity", "ne doit pas etre un mot reserve SQL/MariaDB")

    table = data.get("table")
    if isinstance(table, str) and not _is_snake_case(table):
        _add_issue(issues, "table", "doit etre un nom snake_case valide")
    elif isinstance(table, str) and _is_sql_reserved_word(table):
        _add_issue(issues, "table", "ne doit pas etre un mot reserve SQL/MariaDB")

    fields = data.get("fields")
    if not isinstance(fields, list):
        return

    field_names: dict[str, int] = {}
    column_names: dict[str, int] = {}
    primary_key_indexes: list[int] = []

    for index, field in enumerate(fields):
        if not isinstance(field, dict):
            continue
        _validate_field_consistency(field, index, issues)

        name = field.get("name")
        if isinstance(name, str):
            if name in field_names:
                _add_issue(
                    issues,
                    f"fields[{index}].name",
                    f'doit etre unique (deja utilise par fields[{field_names[name]}].name)',
                )
            else:
                field_names[name] = index

        column = field.get("column")
        if isinstance(column, str):
            if column in column_names:
                _add_issue(
                    issues,
                    f"fields[{index}].column",
                    f'doit etre unique (deja utilise par fields[{column_names[column]}].column)',
                )
            else:
                column_names[column] = index

        if field.get("primary_key") is True:
            primary_key_indexes.append(index)

    if not primary_key_indexes:
        _add_issue(issues, "fields", "une cle primaire est requise")
    elif len(primary_key_indexes) > 1:
        indexes = ", ".join(f"fields[{index}]" for index in primary_key_indexes)
        _add_issue(issues, "fields", f"une seule cle primaire est autorisee (trouvees: {indexes})")


def _validate_field_consistency(field: dict[str, Any], index: int, issues: list[EntityDefinitionIssue]) -> None:
    path = f"fields[{index}]"
    name = field.get("name")
    column = field.get("column")
    python_type = field.get("python_type")
    sql_type = field.get("sql_type")
    nullable = field.get("nullable")
    primary_key = field.get("primary_key")
    auto_increment = field.get("auto_increment")
    constraints = field.get("constraints")

    if isinstance(name, str) and not _is_snake_case(name):
        _add_issue(issues, f"{path}.name", "doit etre un nom snake_case valide")

    if isinstance(column, str):
        if not _is_sql_identifier(column):
            _add_issue(issues, f"{path}.column", "doit etre un identifiant SQL valide")
        elif _is_sql_reserved_word(column):
            _add_issue(issues, f"{path}.column", "ne doit pas etre un mot reserve SQL/MariaDB")

    if isinstance(python_type, str) and python_type not in ALLOWED_PYTHON_TYPES:
        _add_issue(
            issues,
            f"{path}.python_type",
            "doit etre l'un de: int, str, float, bool, date, datetime",
        )

    if isinstance(python_type, str) and isinstance(sql_type, str):
        if not _python_sql_compatible(python_type, sql_type):
            _add_issue(
                issues,
                f"{path}.sql_type",
                f"n'est pas compatible avec python_type={python_type!r}",
            )

    if primary_key is True and nullable is True:
        _add_issue(issues, f"{path}.nullable", "une cle primaire ne peut pas etre nullable")

    if auto_increment is True:
        if primary_key is not True:
            _add_issue(issues, f"{path}.auto_increment", "est autorise uniquement sur une cle primaire")
        if python_type != "int":
            _add_issue(issues, f"{path}.auto_increment", "requiert python_type='int'")
        if isinstance(sql_type, str) and _sql_family(sql_type) != "int":
            _add_issue(issues, f"{path}.auto_increment", "requiert un sql_type entier compatible")

    if isinstance(constraints, dict) and isinstance(python_type, str):
        _validate_constraints(constraints, python_type, path, issues)

    if "default" in field and isinstance(python_type, str):
        _validate_default(field["default"], python_type, nullable, path, issues)


def _validate_constraints(
    constraints: dict[str, Any],
    python_type: str,
    path: str,
    issues: list[EntityDefinitionIssue],
) -> None:
    if "not_empty" in constraints:
        value = constraints["not_empty"]
        if not isinstance(value, bool):
            _add_issue(issues, f"{path}.constraints.not_empty", "doit etre un booleen")
        elif python_type != "str":
            _add_issue(issues, f"{path}.constraints.not_empty", "est reserve aux champs de type str")

    for key in ("min_length", "max_length"):
        if key in constraints:
            value = constraints[key]
            if not _is_int_but_not_bool(value):
                _add_issue(issues, f"{path}.constraints.{key}", "doit etre un entier")
            elif value < 0:
                _add_issue(issues, f"{path}.constraints.{key}", "doit etre superieur ou egal a 0")
            if python_type != "str":
                _add_issue(issues, f"{path}.constraints.{key}", "est reserve aux champs de type str")

    for key in ("min_value", "max_value"):
        if key in constraints:
            value = constraints[key]
            if not _is_number_but_not_bool(value):
                _add_issue(issues, f"{path}.constraints.{key}", "doit etre un nombre")
            if python_type not in {"int", "float"}:
                _add_issue(issues, f"{path}.constraints.{key}", "est reserve aux champs de type int ou float")

    if "pattern" in constraints:
        value = constraints["pattern"]
        if not isinstance(value, str):
            _add_issue(issues, f"{path}.constraints.pattern", "doit etre une chaine")
        else:
            try:
                re.compile(value)
            except re.error as exc:
                _add_issue(issues, f"{path}.constraints.pattern", f"regex invalide: {exc}")
        if python_type != "str":
            _add_issue(issues, f"{path}.constraints.pattern", "est reserve aux champs de type str")


def _validate_default(
    value: Any,
    python_type: str,
    nullable: Any,
    path: str,
    issues: list[EntityDefinitionIssue],
) -> None:
    if value is None:
        if nullable is not True:
            _add_issue(issues, f"{path}.default", "null n'est autorise que si nullable vaut true")
        return

    if python_type == "str":
        if not isinstance(value, str):
            _add_issue(issues, f"{path}.default", "doit etre une chaine compatible avec python_type='str'")
        return

    if python_type == "int":
        if not _is_int_but_not_bool(value):
            _add_issue(issues, f"{path}.default", "doit etre un entier compatible avec python_type='int'")
        return

    if python_type == "float":
        if not _is_number_but_not_bool(value):
            _add_issue(issues, f"{path}.default", "doit etre un nombre compatible avec python_type='float'")
        return

    if python_type == "bool":
        if not _is_bool(value):
            _add_issue(issues, f"{path}.default", "doit etre un booleen compatible avec python_type='bool'")
        return

    if python_type == "date":
        if not _is_iso_date_string(value):
            _add_issue(
                issues,
                f"{path}.default",
                "doit etre une chaine ISO compatible avec python_type='date'",
            )
        return

    if python_type == "datetime":
        if not _is_iso_datetime_string(value):
            _add_issue(
                issues,
                f"{path}.default",
                "doit etre une chaine ISO compatible avec python_type='datetime'",
            )
