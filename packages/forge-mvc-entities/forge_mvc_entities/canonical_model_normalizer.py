# pyright: strict
"""Normaliseur canonique → structure interne build:model.

Traduit une entité au format canonique (schema_version: "1.0") en un dict
compatible avec le format legacy attendu par validate_entity_definition()
et les générateurs build_entity_sql() / build_entity_base().

Ce module est une couche de transition interne, vouée à disparaître (ADR-086).
La structure produite n'est pas un format public — elle suit le format legacy
attendu par normalize_entity_definition() dans validation.py. Le mapping type
canonique vers sql_type/python_type/column est délégué au service partagé
`field_resolver` (source unique, ADR-086) ; ce module n'assure plus que
l'assemblage du dict et la synthèse des champs système (id, horodatages).

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

from forge_mvc_entities.field_resolver import (
    IDENTITY_COLUMN,
    SLUG_MAX_LENGTH,
    CanonicalNormalizationError as CanonicalNormalizationError,
    column_of,
    dialect,
    nullable_of,
    numeric_constraints_of,
    resolve_sql_and_python_type,
    unique_of,
)


def column_for_field(field: dict[str, Any]) -> str:
    """Nom de colonne SQL d'un champ de contrat d'entité (ADR-069, ADR-077).

    Fonction publique consommée par `forge-mvc-fixtures` (`make-factory`) pour
    échafauder les colonnes réelles. Délègue au service `field_resolver`, source
    unique du mapping champ vers colonne (ADR-086).
    """
    return column_of(field)


def _id_field() -> dict[str, Any]:
    return {
        "name": "id",
        "column": IDENTITY_COLUMN,
        "sql_type": dialect().identity_type(),
        "python_type": "int",
        "nullable": False,
        "primary_key": True,
        "auto_increment": True,
        "constraints": {},
        "unique": False,
    }


def _system_datetime_field(
    name: str, *, nullable: bool, managed: str | None = None
) -> dict[str, Any]:
    field: dict[str, Any] = {
        "name": name,
        "column": column_of({"name": name}),
        "sql_type": dialect().simple_type("datetime"),
        "python_type": "datetime",
        "nullable": nullable,
        "primary_key": False,
        "auto_increment": False,
        "constraints": {},
        "unique": False,
    }
    # ADR-081 : horodatage géré par le framework (posé par le modèle, exclu du
    # formulaire). La valeur distingue la stabilité à l'édition (created stable,
    # updated réécrit à chaque UPDATE).
    if managed is not None:
        field["managed"] = managed
    return field


def _normalize_field(field: dict[str, Any]) -> dict[str, Any]:
    name = field["name"]
    forge_type = field.get("type", "")

    sql_type, python_type = resolve_sql_and_python_type(field)

    # Dérivations par champ déléguées au service field_resolver (ADR-086,
    # source unique) : nullabilité (ADR-013), bornes min/max, contrainte unique,
    # colonne (ADR-069/077).
    normalized: dict[str, Any] = {
        "name": name,
        "column": column_for_field(field),
        "sql_type": sql_type,
        "python_type": python_type,
        "nullable": nullable_of(field),
        "primary_key": False,
        "auto_increment": False,
        "constraints": numeric_constraints_of(field),
        "unique": unique_of(field),
    }

    # Métadonnée de relation : l'entité cible référencée (contrat complet).
    if forge_type == "foreign_key" and "references" in field:
        normalized["references"] = field["references"]

    # Type slug : widget SlugField + longueur de colonne (ADR-017).
    if forge_type == "slug":
        normalized["form"] = {"field": "slug"}
        normalized["constraints"]["max_length"] = SLUG_MAX_LENGTH
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
        fields.append(_system_datetime_field("created_at", nullable=False, managed="timestamp_created"))
        fields.append(_system_datetime_field("updated_at", nullable=False, managed="timestamp_updated"))

    if options.get("soft_delete"):
        fields.append(_system_datetime_field("deleted_at", nullable=True, managed="soft_delete"))

    result: dict[str, Any] = {
        "entity": name,
        "table": table,
        "fields": fields,
    }
    if description:
        result["description"] = description

    return result
