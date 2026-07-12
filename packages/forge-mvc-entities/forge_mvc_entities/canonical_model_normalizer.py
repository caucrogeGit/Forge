# pyright: strict
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

from core.database.backend import Dialect, get_backend


_DEFAULT_STRING_LENGTH = 255

# Type Python (runtime) d'un type Forge simple. Non dialectal : il ne dépend
# pas du SGBD. Le type SQL correspondant, lui, vient du dialecte du backend
# actif (ADR-054), via dialect.simple_type().
_SIMPLE_PYTHON_TYPE: dict[str, str] = {
    "text":        "str",
    "integer":     "int",
    "big_integer": "int",
    "float":       "float",
    "boolean":     "bool",
    "date":        "date",
    "datetime":    "datetime",
    "email":       "str",
    "password":    "str",
    "slug":        "str",
    "json":        "str",
}


def _dialect() -> Dialect:
    """Dialecte SQL du backend BDD actif (ADR-054)."""
    return get_backend().dialect

# Longueur de colonne d'un slug URL (ADR-017 D3) — alignée avec SlugField.
_SLUG_MAX_LENGTH = 180


class CanonicalNormalizationError(ValueError):
    """Erreur lors de la normalisation d'une entité canonique."""


def _column_from_name(name: str) -> str:
    return "".join(part.capitalize() for part in name.split("_") if part)


def column_for_field(field: dict[str, Any]) -> str:
    """Nom de colonne SQL d'un champ de contrat d'entite (ADR-069, ADR-077).

    Convention canonique, source unique du mapping champ vers colonne :

    - un champ `foreign_key` garde son nom snake_case (`annee_scolaire_id`), en
      coherence avec la colonne emise par `build:model` ;
    - tout autre champ passe en PascalCase (`user_id` vers `UserId`,
      `nom` vers `Nom`).

    La cle primaire (`Id`) n'est pas un champ de contrat : elle n'est pas
    concernee. Fonction publique consommee par `forge-mvc-fixtures`
    (`make-factory`) pour echafauder les colonnes reelles (ADR-077).
    """
    name = str(field.get("name", ""))
    if str(field.get("type", "")) == "foreign_key":
        return name
    return _column_from_name(name)


def _build_sql_and_python_type(forge_type: str, field: dict[str, Any]) -> tuple[str, str]:
    field_name = field.get("name", "?")
    dialect = _dialect()

    if forge_type == "string":
        max_length = field.get("max_length", _DEFAULT_STRING_LENGTH)
        if not isinstance(max_length, int) or isinstance(max_length, bool) or max_length <= 0:
            raise CanonicalNormalizationError(
                f"Champ '{field_name}' : max_length doit être un entier positif pour type 'string'."
            )
        return dialect.string_type(max_length), "str"

    if forge_type == "decimal":
        precision = field.get("precision")
        scale = field.get("scale")
        if precision is None or scale is None:
            raise CanonicalNormalizationError(
                f"Champ '{field_name}' : precision et scale sont requis pour type 'decimal'."
            )
        return dialect.decimal_type(precision, scale), "float"

    if forge_type == "foreign_key":
        # Clé étrangère de première classe (ADR-069) : même type que la PK visée.
        # Toutes les PK Forge sont `identity_type()` (BIGINT UNSIGNED sur MariaDB),
        # donc une FK vers n'importe quelle entité adopte ce type, backend-agnostique.
        return dialect.identity_type(), "int"

    if forge_type in _SIMPLE_PYTHON_TYPE:
        return dialect.simple_type(forge_type), _SIMPLE_PYTHON_TYPE[forge_type]

    raise CanonicalNormalizationError(
        f"Champ '{field_name}' : type Forge inconnu : {forge_type!r}."
    )


def _id_field() -> dict[str, Any]:
    return {
        "name": "id",
        "column": "Id",
        "sql_type": _dialect().identity_type(),
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
        "sql_type": _dialect().simple_type("datetime"),
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

    # ADR-069 / ADR-077 : mapping champ vers colonne, source unique.
    column = column_for_field(field)

    normalized: dict[str, Any] = {
        "name": name,
        "column": column,
        "sql_type": sql_type,
        "python_type": python_type,
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": constraints,
        "unique": bool(field.get("unique", False)),
    }

    # Métadonnée de relation : l'entité cible référencée (contrat complet).
    if forge_type == "foreign_key" and "references" in field:
        normalized["references"] = field["references"]

    # Type slug : widget SlugField + longueur de colonne (ADR-017).
    if forge_type == "slug":
        normalized["form"] = {"field": "slug"}
        normalized["constraints"]["max_length"] = _SLUG_MAX_LENGTH
        # Slug auto-généré depuis un champ source (étape B) : propagé tel quel,
        # consommé par le générateur CRUD (form exclu, slugify à la création).
        if "source" in field:
            normalized["source"] = field["source"]

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
    options: dict[str, Any] = entity.get("options") or {}

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
