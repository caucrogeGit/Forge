# pyright: strict
"""Forge workflow — statuts et transitions applicatives.

Opt-in officiel Forge livre separement depuis Forge 2.6.0 (ADR-004).

Depuis `WORKFLOW-HOOKS-001`, le paquet sait aussi **appliquer** une
transition dans un ordre garanti, avec des points d'accroche avant et
apres. Il ne persiste toujours rien : l'ecriture est fournie par
l'application, seule a savoir ou son statut est range.
"""

from __future__ import annotations

from forge_mvc_workflow.hooks import (
    TransitionCommit,
    TransitionEvent,
    TransitionHook,
    apply_transition,
)
from forge_mvc_workflow.jinja import (
    make_workflow_jinja_helpers,
    workflow_status_badge,
    workflow_status_badge_class,
    workflow_status_color,
    workflow_status_label,
)
from forge_mvc_workflow.status import (
    WorkflowStatus,
    WorkflowStatusError,
    find_status,
    make_status,
    normalize_status_name,
    validate_status_name,
    validate_statuses,
)
from forge_mvc_workflow.transitions import (
    WorkflowTransition,
    WorkflowTransitionError,
    can_transition,
    get_available_transitions,
    make_transition,
    validate_transitions,
)

__version__ = "1.0.0rc7"

__all__ = [
    # Application d'une transition (WORKFLOW-HOOKS-001)
    "apply_transition",
    "TransitionEvent",
    "TransitionHook",
    "TransitionCommit",
    "WorkflowStatus",
    "WorkflowStatusError",
    "find_status",
    "make_status",
    "normalize_status_name",
    "validate_status_name",
    "validate_statuses",
    "WorkflowTransition",
    "WorkflowTransitionError",
    "can_transition",
    "get_available_transitions",
    "make_transition",
    "validate_transitions",
    "make_workflow_jinja_helpers",
    "workflow_status_badge",
    "workflow_status_badge_class",
    "workflow_status_color",
    "workflow_status_label",
]
