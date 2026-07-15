# pyright: strict
"""Normaliseur canonique → structure interne build:model.

Traduit une entité au format canonique (schema_version: "1.0") en un dict
compatible avec le format legacy attendu par validate_entity_definition()
et les générateurs build_entity_sql() / build_entity_base().

Ce module est une couche de transition interne, vouée à disparaître (ADR-086).
La structure produite n'est pas un format public — elle suit le format legacy
attendu par normalize_entity_definition() dans validation.py. Toute la
résolution de champs (mapping de types, colonnes, synthèse des champs système)
est déléguée au service partagé `field_resolver` (source unique, ADR-086) ; ce
module n'assure plus que l'assemblage racine (entity, table, description).

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
    CanonicalNormalizationError as CanonicalNormalizationError,
    column_of,
    resolve_entity_fields,
)


def column_for_field(field: dict[str, Any]) -> str:
    """Nom de colonne SQL d'un champ de contrat d'entité (ADR-069, ADR-077).

    Fonction publique consommée par `forge-mvc-fixtures` (`make-factory`) pour
    échafauder les colonnes réelles. Délègue au service `field_resolver`, source
    unique du mapping champ vers colonne (ADR-086).
    """
    return column_of(field)


def normalize_canonical_entity_for_model_build(entity: dict[str, Any]) -> dict[str, Any]:
    """Traduit une entité canonique (schema_version 1.0) en dict legacy interne.

    Compatible avec validate_entity_definition() et les générateurs
    build_entity_sql() / build_entity_base(). Ne modifie pas les fichiers sources.

    L'énumération des champs (id synthétique, champs métier, champs système)
    est déléguée à `field_resolver.resolve_entity_fields` (source unique,
    ADR-086). Ce module n'assure plus que l'assemblage racine (entity, table,
    description). Les index (entity["indexes"]) sont ignorés — build:model ne
    les supporte pas encore.
    """
    result: dict[str, Any] = {
        "entity": entity.get("name", ""),
        "table": entity.get("table", ""),
        "fields": resolve_entity_fields(entity),
    }
    description = entity.get("description", "")
    if description:
        result["description"] = description

    return result
