# pyright: strict
"""Événements statistiques génériques pour Forge.

Les noms d'événements sont de simples chaînes snake_case définies par l'application.
Forge ne préconise aucune liste de noms — ce principe est conforme à la Charte Forge
(Principe 1 : le framework n'est pas l'application).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any


_VALID_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SAFE_NORMALIZE_RE = re.compile(r"[\s\-]+")
_UNSAFE_CHARS_RE = re.compile(r"[^a-z0-9_\s\-]")


class StatsEventError(ValueError):
    pass


@dataclass(frozen=True)
class StatsEvent:
    name: str
    label: str = ""
    category: str = "general"
    metadata: dict[str, Any] = field(default_factory=dict[str, Any])

    def __post_init__(self) -> None:
        validated_name = validate_event_name(self.name)
        object.__setattr__(self, "name", validated_name)
        if not self.label:
            object.__setattr__(self, "label", validated_name)
        if not self.category:
            object.__setattr__(self, "category", "general")
        if self.metadata is None:  # pyright: ignore[reportUnnecessaryComparison]
            object.__setattr__(self, "metadata", {})
        if not isinstance(self.metadata, dict):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise StatsEventError(
                f"metadata doit être un dictionnaire, reçu : {type(self.metadata).__name__}."
            )


def normalize_event_name(value: str) -> str:
    """Convert a raw string to a valid snake_case event name.

    Spaces and hyphens are converted to underscores.
    Any other non-alphanumeric character raises StatsEventError.
    """
    if not isinstance(value, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsEventError("Le nom d'événement doit être une chaîne.")
    lowered = value.strip().lower()
    if _UNSAFE_CHARS_RE.search(lowered):
        raise StatsEventError(
            f"Le nom d'événement '{value}' contient des caractères non autorisés. "
            "Utilisez uniquement des lettres, des chiffres, des espaces et des tirets."
        )
    normalized = _SAFE_NORMALIZE_RE.sub("_", lowered)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def validate_event_name(value: str) -> str:
    """Validate and return a normalized event name, or raise StatsEventError."""
    if not isinstance(value, str):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsEventError("Le nom d'événement doit être une chaîne.")
    if not value or not value.strip():
        raise StatsEventError("Le nom d'événement ne peut pas être vide.")
    normalized = normalize_event_name(value)
    if not normalized:
        raise StatsEventError(
            f"Le nom d'événement '{value}' est invalide après normalisation."
        )
    if not _VALID_NAME_RE.match(normalized):
        raise StatsEventError(
            f"Le nom d'événement '{value}' est invalide. "
            "Format attendu : lettres minuscules, chiffres et tirets bas, "
            "commençant par une lettre."
        )
    return normalized


def make_event(
    name: str,
    label: str = "",
    category: str = "general",
    metadata: dict[str, Any] | None = None,
) -> StatsEvent:
    """Create a validated StatsEvent."""
    return StatsEvent(
        name=name,
        label=label,
        category=category,
        metadata=metadata if metadata is not None else {},
    )


def validate_event(event: StatsEvent) -> StatsEvent:
    """Validate an existing StatsEvent and return it, or raise StatsEventError."""
    if not isinstance(event, StatsEvent):  # pyright: ignore[reportUnnecessaryIsInstance]
        raise StatsEventError(
            f"Un StatsEvent est attendu, reçu : {type(event).__name__}."
        )
    return event
