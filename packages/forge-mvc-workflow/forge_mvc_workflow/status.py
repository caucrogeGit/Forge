"""Statuts génériques de workflow pour Forge."""

from __future__ import annotations

import re
from dataclasses import dataclass


_VALID_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")
_SAFE_NORMALIZE_RE = re.compile(r"[\s\-]+")
_UNSAFE_CHARS_RE = re.compile(r"[^a-z0-9_\s\-]")


class WorkflowStatusError(ValueError):
    pass


@dataclass
class WorkflowStatus:
    name: str
    label: str = ""
    color: str = ""
    is_initial: bool = False
    is_final: bool = False

    def __post_init__(self) -> None:
        self.name = validate_status_name(self.name)
        if not self.label:
            self.label = self.name


def normalize_status_name(value: str) -> str:
    """Convert a raw string to a valid snake_case status name.

    Only spaces and hyphens are converted to underscores. Any other
    non-alphanumeric character causes a WorkflowStatusError.
    """
    if not isinstance(value, str):
        raise WorkflowStatusError("Le nom de statut doit être une chaîne.")
    lowered = value.strip().lower()
    if _UNSAFE_CHARS_RE.search(lowered):
        raise WorkflowStatusError(
            f"Le nom de statut '{value}' contient des caractères non autorisés. "
            "Utilisez uniquement des lettres, des chiffres, des espaces et des tirets."
        )
    normalized = _SAFE_NORMALIZE_RE.sub("_", lowered)
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized


def validate_status_name(value: str) -> str:
    """Validate and return a normalized status name, or raise WorkflowStatusError."""
    if not isinstance(value, str):
        raise WorkflowStatusError("Le nom de statut doit être une chaîne.")
    if not value or not value.strip():
        raise WorkflowStatusError("Le nom de statut ne peut pas être vide.")
    normalized = normalize_status_name(value)
    if not normalized:
        raise WorkflowStatusError(
            f"Le nom de statut '{value}' est invalide après normalisation."
        )
    if not _VALID_NAME_RE.match(normalized):
        raise WorkflowStatusError(
            f"Le nom de statut '{value}' contient des caractères non autorisés. "
            "Utilisez uniquement des lettres minuscules, des chiffres et des tirets bas."
        )
    return normalized


def make_status(
    name: str,
    label: str = "",
    color: str = "",
    is_initial: bool = False,
    is_final: bool = False,
) -> WorkflowStatus:
    """Create a WorkflowStatus with validated and normalized name."""
    return WorkflowStatus(
        name=name,
        label=label,
        color=color,
        is_initial=is_initial,
        is_final=is_final,
    )


def validate_statuses(statuses: list[WorkflowStatus]) -> list[WorkflowStatus]:
    """Validate a list of statuses: no duplicates, at most one initial."""
    seen_names: set[str] = set()
    initial_count = 0
    for status in statuses:
        if status.name in seen_names:
            raise WorkflowStatusError(
                f"Statut en doublon : '{status.name}'."
            )
        seen_names.add(status.name)
        if status.is_initial:
            initial_count += 1
    if initial_count > 1:
        raise WorkflowStatusError(
            f"{initial_count} statuts marqués comme initiaux. "
            "Au plus un statut peut être initial."
        )
    return statuses


def find_status(
    statuses: list[WorkflowStatus], name: str
) -> WorkflowStatus | None:
    """Return the status with matching name, or None if not found."""
    for status in statuses:
        if status.name == name:
            return status
    return None
