"""Helpers Jinja d'affichage de statuts workflow pour Forge."""

from __future__ import annotations

from markupsafe import Markup, escape

from .status import WorkflowStatus


_BASE = "inline-flex items-center rounded-full px-2 py-1 text-xs font-medium"

_BADGE_CLASSES: dict[str, str] = {
    "gray":   f"{_BASE} bg-gray-100 text-gray-700",
    "blue":   f"{_BASE} bg-blue-100 text-blue-700",
    "green":  f"{_BASE} bg-green-100 text-green-700",
    "yellow": f"{_BASE} bg-yellow-100 text-yellow-700",
    "red":    f"{_BASE} bg-red-100 text-red-700",
    "purple": f"{_BASE} bg-purple-100 text-purple-700",
}

_DEFAULT_COLOR = "gray"


def workflow_status_label(status: WorkflowStatus | str | None) -> str:
    """Return the display label for a status.

    Accepts a WorkflowStatus, a plain string, or None.
    Falls back to the name if label is empty, or to an empty string for None.
    """
    if isinstance(status, WorkflowStatus):
        return status.label or status.name
    if status is None:
        return ""
    return str(status)


def workflow_status_color(status: WorkflowStatus | str | None) -> str:
    """Return the color string for a status, defaulting to 'gray'."""
    if isinstance(status, WorkflowStatus):
        return status.color or _DEFAULT_COLOR
    return _DEFAULT_COLOR


def workflow_status_badge_class(status: WorkflowStatus | str | None) -> str:
    """Return Tailwind CSS classes for a status badge.

    Unmapped colors fall back to the gray palette.
    """
    color = workflow_status_color(status)
    return _BADGE_CLASSES.get(color, _BADGE_CLASSES[_DEFAULT_COLOR])


def workflow_status_badge(status: WorkflowStatus | str | None) -> Markup:
    """Return a safe HTML <span> badge for a status.

    Marked as Markup so Jinja2 does not double-escape it.
    """
    label = workflow_status_label(status)
    classes = workflow_status_badge_class(status)
    return Markup(f'<span class="{classes}">{escape(label)}</span>')


def make_workflow_jinja_helpers() -> dict[str, object]:
    """Return a dict of workflow helpers ready for injection into a Jinja2 env."""
    return {
        "workflow_status_label": workflow_status_label,
        "workflow_status_color": workflow_status_color,
        "workflow_status_badge_class": workflow_status_badge_class,
        "workflow_status_badge": workflow_status_badge,
    }
