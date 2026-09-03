# pyright: strict
"""forge-mvc-entities — moteur d'entites, opt-in (extrait du coeur, ADR-070).

Generation et modelisation d'entites et de relations : `make:entity`,
`make:relation` (`many_to_one` et `many_to_many`), normaliseur canonique,
validation, `build:model`, generation de migrations, `make:crud`, provisioning
`db:config` / `db:init` / `db:apply`, et le service pivot enrichi + `make:pivot-crud`
(herites de `forge-mvc-pivot`, absorbe par cet opt-in).

Cet opt-in depend du contrat `Dialect` expose par le coeur (`core.database`),
jamais d'un backend concret : il reste independant du SGBD. Il consomme aussi les
schemas d'entites/relations, qui restent des *contrats du coeur* (`cli.schemas`,
ADR-058), a l'image du contrat `Dialect`.

L'API du paquet est faite de ses sous-modules (un par commande : `make_entity`,
`make_relation`, `make_crud`, `model`, `entity_validate`, `entity_doc`,
`migrations`, `db_apply`, `db_init`, `db_config`, `make_pivot_crud`, ...) et de
leurs fonctions publiques (`validation.validate_entity_definition`,
`relations.validate_relations_definition`, ...). On importe le sous-module voulu.

L'API runtime du pivot enrichi (`many_to_many` avec attributs), absorbee de
`forge-mvc-pivot` (ADR-021, repliee ici par ADR-070), est re-exportee a la racine
pour l'usage applicatif (`from forge_mvc_entities import PivotAdvancedService`).
"""
from __future__ import annotations

from forge_mvc_entities.canonical_model_normalizer import column_for_field
from forge_mvc_entities.crud.utils import pk_field
from forge_mvc_entities.service import (
    PivotAdvancedService,
    PivotConstraintError,
    PivotFieldConstraint,
    PivotFormError,
    PivotRow,
    pivot_error_to_form_error,
)
from forge_mvc_entities.validation import to_snake

from forge_mvc_entities.validators import (
    EntityValidationError,
    EntityValidator,
    ValidationIssue,
    ValidationReport,
    clear_entity_validators,
    ensure_entity_data,
    register_entity_validator,
    registered_validators,
    unregister_entity_validator,
    validate_entity_data,
)

__all__ = [
    # Validation métier déclarable (ENTITIES-BUSINESS-VALIDATION-001)
    "register_entity_validator",
    "unregister_entity_validator",
    "registered_validators",
    "clear_entity_validators",
    "validate_entity_data",
    "ensure_entity_data",
    "ValidationIssue",
    "ValidationReport",
    "EntityValidationError",
    "EntityValidator",
    "PivotAdvancedService",
    "PivotConstraintError",
    "PivotFieldConstraint",
    "PivotFormError",
    "PivotRow",
    "column_for_field",
    "pivot_error_to_form_error",
    "pk_field",
    "to_snake",
]

__version__ = "1.0.0rc7"
