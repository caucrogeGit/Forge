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

from typing import Any, cast

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
    description, indexes).

    Les index déclarés sont désormais portés. Ils s'arrêtaient ici : le schéma
    JSON les acceptait, la validation sémantique vérifiait que leurs champs
    existent, et plus rien ne les regardait. Une contrainte d'unicité composite
    passait donc la validation sans jamais atteindre la base
    (`ENTITIES-UNIQUE-COMPOSITE-001`).
    """
    result: dict[str, Any] = {
        "entity": entity.get("name", ""),
        "table": entity.get("table", ""),
        "fields": resolve_entity_fields(entity),
    }
    description = entity.get("description", "")
    if description:
        result["description"] = description

    indexes = _normalize_indexes(entity)
    if indexes:
        result["indexes"] = indexes

    return result


def _normalize_indexes(entity: "dict[str, Any]") -> "list[dict[str, Any]]":
    """Index déclarés, ramenés à la forme canonique et aux colonnes réelles.

    Le contrat nomme des **champs**, la base connaît des **colonnes** : la
    correspondance passe par les champs résolus, un champ pouvant porter un nom
    de colonne différent du sien.

    Un index dont un champ est inconnu est écarté silencieusement ici : c'est la
    validation sémantique qui le signale, avec son chemin et son message, et le
    faire lever ici doublerait l'erreur sans rien ajouter.
    """
    declares = entity.get("indexes")
    if not isinstance(declares, list):
        return []

    colonne_par_champ = {
        champ["name"]: champ["column"] for champ in resolve_entity_fields(entity)
    }

    normalises: list[dict[str, Any]] = []
    for declare in cast("list[Any]", declares):
        if not isinstance(declare, dict):
            continue
        index = cast("dict[str, Any]", declare)
        nom = index.get("name")
        champs = index.get("fields")
        if not isinstance(nom, str) or not isinstance(champs, list):
            continue
        colonnes = [
            colonne_par_champ[champ]
            for champ in cast("list[Any]", champs)
            if isinstance(champ, str) and champ in colonne_par_champ
        ]
        if len(colonnes) != len(cast("list[Any]", champs)):
            continue
        normalises.append({
            "name": nom,
            "columns": colonnes,
            "unique": index.get("unique") is True,
        })
    return normalises
