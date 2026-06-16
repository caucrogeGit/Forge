# pyright: strict
from typing import Any


class Validator:
    """
    Classe de base pour la validation de formulaires.

    Usage :
        class MonValidator(Validator):
            def __init__(self, data):
                super().__init__()
                self.required(data.get("nom", ""), "Nom")
                self.max_length(data.get("nom", ""), 40, "Nom")
    """

    def __init__(self) -> None:
        self._errors: list[str] = []

    def required(self, value: Any, label: str) -> "Validator":
        """Vérifie que le champ est non vide."""
        if not value or not str(value).strip():
            self._errors.append(f"Le champ {label} est obligatoire.")
        return self

    def max_length(self, value: Any, max_len: int, label: str) -> "Validator":
        """Vérifie que le champ ne dépasse pas une longueur maximale."""
        if value and len(str(value)) > max_len:
            self._errors.append(f"Le champ {label} ne doit pas dépasser {max_len} caractères.")
        return self

    def add_error(self, message: str) -> "Validator":
        """Ajoute une erreur manuellement (ex: doublon BDD)."""
        self._errors.append(message)
        return self

    def is_valid(self) -> bool:
        return len(self._errors) == 0

    def errors(self) -> list[str]:
        """Retourne la liste brute des messages d'erreur."""
        return list(self._errors)
