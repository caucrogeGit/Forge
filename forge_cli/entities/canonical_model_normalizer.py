"""Normaliseur canonique → structure interne build:model.

Traduit une entité au format canonique (schema_version: "1.0") en un dict
compatible avec le format legacy attendu par validate_entity_definition()
et les générateurs build_entity_sql() / build_entity_base().

Ce module est une couche de transition interne.
La structure produite n'est pas un format public — elle suit le format legacy
attendu par normalize_entity_definition() dans validation.py.

Limites documentées :
- Les index (indexes[]) sont ignorés : build:model ne les gère pas encore.
- Les relations sont hors périmètre : elles restent dans relations.json.
- string sans max_length : par défaut VARCHAR(255), documenté comme conservateur.
- decimal sans precision/scale : erreur explicite levée immédiatement.
- boolean → BOOLEAN (et non TINYINT(1)) : TINYINT(1) mappe vers python_type='int'
  dans _sql_family(), ce qui invaliderait la vérification de compatibilité sql/python.
"""

from __future__ import annotations

from typing import Any


_DEFAULT_STRING_LENGTH = 255

_SIMPLE_TYPE_MAP: dict[str, tuple[str, str]] = {
    "text":        ("TEXT",          "str"),
    "integer":     ("INT",           "int"),
    "big_integer": ("BIGINT",        "int"),
    "float":       ("DOUBLE",        "float"),
    "boolean":     ("BOOLEAN",       "bool"),
    "date":        ("DATE",          "date"),
    "datetime":    ("DATETIME",      "datetime"),
    "email":       ("VARCHAR(255)",  "str"),
    "password":    ("VARCHAR(255)",  "str"),
    "slug":        ("VARCHAR(180)",  "str"),
    "json":        ("LONGTEXT",      "str"),
}

# Longueur de colonne d'un slug URL (ADR-017 D3) — alignée avec SlugField.
_SLUG_MAX_LENGTH = 180


class CanonicalNormalizationError(ValueError):
    """Erreur lors de la normalisation d'une entité canonique."""


def _column_from_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def _build_sql_and_python_type(forge_type: str, field: dict[str, Any]) -> tuple[str, str]:
    field_name = field.get("name", "?")

    if forge_type == "string":
        max_length = field.get("max_length", _DEFAULT_STRING_LENGTH)
        if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length <= 0:
            raise CanonicalNormalizationError(
                f"Champ '{field_name}' : max_length doit être un entier positif pour type 'string'."
            )
        return f"VARCHAR({max_length})", "str"

    if forge_type == "decimal":
        precision = field.get("precision")
        scale = field.get("scale")
        if precision is None or scale is None:
            raise CanonicalNormalizationError(
                f"Champ '{field_name}' : precision et scale sont requis pour type 'decimal'."
            )
        return f"DECIMAL({precision},{scale})", "float"

    if forge_type in _SIMPLE_TYPE_MAP:
        return _SIMPLE_TYPE_MAP[forge_type]

    raise CanonicalNormalizationError(
        f"Champ '{field_name}' : type Forge inconnu : {forge_type!r}."
    )


def _id_field() -> dict[str, Any]:
    return {
        "name": "id",
        "column": "Id",
        "sql_type": "BIGINT UNSIGNED",
        "python_type": "int",
        "nullable": False,
        "primary_key": True,
        "auto_increment": True,
        "constraints": {},
        "unique": False,
    }


def _system_datetime_field(name: str, *, nullable: bool) -> dict[str, Any]:
    return {
        "name": name,
        "column": _column_from_name(name),
        "sql_type": "DATETIME",
        "python_type": "datetime",
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": {},
        "unique": False,
    }


def _normalize_field(field: dict[str, Any]) -> dict[str, Any]:
    name = field["name"]
    forge_type = field.get("type", "")

    sql_type, python_type = _build_sql_and_python_type(forge_type, field)

    # ADR-013 : nullable par défaut (True), required prioritaire.
    nullable = bool(field.get("nullable", True))
    if field.get("required") is True:
        nullable = False

    constraints: dict[str, Any] = {}
    if "min" in field and python_type in ("int", "float"):
        constraints["min_value"] = field["min"]
    if "max" in field and python_type in ("int", "float"):
        constraints["max_value"] = field["max"]

    normalized: dict[str, Any] = {
        "name": name,
        "column": _column_from_name(name),
        "sql_type": sql_type,
        "python_type": python_type,
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": constraints,
        "unique": bool(field.get("unique", False)),
    }

    # Type slug : widget SlugField + longueur de colonne (ADR-017).
    if forge_type == "slug":
        normalized["form"] = {"field": "slug"}
        normalized["constraints"]["max_length"] = _SLUG_MAX_LENGTH

    if "default" in field:
        normalized["default"] = field["default"]

    return normalized


def normalize_canonical_entity_for_model_build(entity: dict[str, Any]) -> dict[str, Any]:
    """Traduit une entité canonique (schema_version 1.0) en dict legacy interne.

    Compatible avec validate_entity_definition() et les générateurs
    build_entity_sql() / build_entity_base(). Ne modifie pas les fichiers sources.

    Les index (entity["indexes"]) sont ignorés — build:model ne les supporte pas encore.
    """
    name = entity.get("name", "")
    table = entity.get("table", "")
    description = entity.get("description", "")
    fields_raw = entity.get("fields", [])
    options = entity.get("options") or {}

    fields: list[dict[str, Any]] = [_id_field()]

    for field in fields_raw:
        if field.get("name") == "id":
            continue
        fields.append(_normalize_field(field))

    if options.get("timestamps"):
        fields.append(_system_datetime_field("created_at", nullable=False))
        fields.append(_system_datetime_field("updated_at", nullable=False))

    if options.get("soft_delete"):
        fields.append(_system_datetime_field("deleted_at", nullable=True))

    result: dict[str, Any] = {
        "entity": name,
        "table": table,
        "fields": fields,
    }
    if description:
        result["description"] = description

    return result
