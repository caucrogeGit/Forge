"""Exceptions de validation Forge."""


class ValidationError(ValueError):
    """Exception centrale de validation V1."""

    def __init__(self, property_name: str, message: str):
        self.property_name = property_name
        self.message = message
        super().__init__(message)
