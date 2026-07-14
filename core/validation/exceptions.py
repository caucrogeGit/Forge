# pyright: strict
"""Exceptions de validation Forge."""


class PropertyValidationError(ValueError):
    """Erreur de validation d'une propriété d'entité (validation V1).

    Nommée distinctement de `core.forms.ValidationError` (erreur de formulaire,
    orientée messages affichables) pour lever la collision de noms : deux
    classes publiques `ValidationError` aux contrats opposés violaient le
    principe 11 (CORE-VALIDATIONERROR-UNIFY-001).
    """

    def __init__(self, property_name: str, message: str) -> None:
        self.property_name = property_name
        self.message = message
        super().__init__(message)
