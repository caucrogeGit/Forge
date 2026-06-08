"""forge-mvc-pivot — Pivot advanced opt-in (extrait du core, ADR-021).

Service de persistance pour tables pivot enrichies (associations many_to_many
avec attributs) et générateur `forge make:pivot-crud`.
"""
from forge_mvc_pivot.service import (
    PivotAdvancedService,
    PivotConstraintError,
    PivotFieldConstraint,
    PivotFormError,
    PivotRow,
    pivot_error_to_form_error,
)

__all__ = [
    "PivotAdvancedService",
    "PivotConstraintError",
    "PivotFieldConstraint",
    "PivotFormError",
    "PivotRow",
    "pivot_error_to_form_error",
]

__version__ = "1.0.0b15"
