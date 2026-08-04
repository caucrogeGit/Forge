# pyright: strict
"""Forge workflow — statuts et transitions applicatives.

Opt-in officiel Forge livre separement depuis Forge 2.6.0 (ADR-004).
"""

from __future__ import annotations

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

__version__ = "1.0.0rc4"

__all__ = [
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
