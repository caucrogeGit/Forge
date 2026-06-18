# pyright: strict
"""Transitions génériques de workflow pour Forge."""

from __future__ import annotations

from dataclasses import dataclass

from .status import WorkflowStatus, WorkflowStatusError, validate_status_name


class WorkflowTransitionError(ValueError):
    pass


@dataclass(frozen=True)
class WorkflowTransition:
    from_status: str
    to_status: str

    def __post_init__(self) -> None:
        try:
            object.__setattr__(self, "from_status", validate_status_name(self.from_status))
            object.__setattr__(self, "to_status", validate_status_name(self.to_status))
        except WorkflowStatusError as exc:
            raise WorkflowTransitionError(str(exc)) from exc
        if self.from_status == self.to_status:
            raise WorkflowTransitionError(
                f"Une transition ne peut pas pointer vers le même statut : '{self.from_status}'."
            )


def make_transition(from_status: str, to_status: str) -> WorkflowTransition:
    """Create a validated WorkflowTransition."""
    return WorkflowTransition(from_status=from_status, to_status=to_status)


def validate_transitions(
    transitions: list[WorkflowTransition],
    statuses: list[WorkflowStatus] | None = None,
) -> list[WorkflowTransition]:
    """Validate a list of transitions.

    Checks:
    - No duplicate (from_status, to_status) pairs.
    - If statuses is provided, all referenced names must exist in that list.
    """
    seen: set[tuple[str, str]] = set()
    for t in transitions:
        key = (t.from_status, t.to_status)
        if key in seen:
            raise WorkflowTransitionError(
                f"Transition en doublon : '{t.from_status}' → '{t.to_status}'."
            )
        seen.add(key)

    if statuses is not None:
        known = {s.name for s in statuses}
        for t in transitions:
            if t.from_status not in known:
                raise WorkflowTransitionError(
                    f"Statut source inconnu : '{t.from_status}'."
                )
            if t.to_status not in known:
                raise WorkflowTransitionError(
                    f"Statut cible inconnu : '{t.to_status}'."
                )

    return transitions


def can_transition(
    transitions: list[WorkflowTransition],
    from_name: str,
    to_name: str,
) -> bool:
    """Return True if a transition from from_name to to_name is defined."""
    from_norm = validate_status_name(from_name)
    to_norm = validate_status_name(to_name)
    return any(t.from_status == from_norm and t.to_status == to_norm for t in transitions)


def get_available_transitions(
    transitions: list[WorkflowTransition],
    from_name: str,
) -> list[WorkflowTransition]:
    """Return all transitions starting from from_name."""
    from_norm = validate_status_name(from_name)
    return [t for t in transitions if t.from_status == from_norm]
