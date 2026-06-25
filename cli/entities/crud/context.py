# pyright: strict
# pyright: reportPrivateUsage=false
# pyright: reportUnusedFunction=false
"""Constants, dataclasses and permission helper for the CRUD generator."""

from __future__ import annotations

from dataclasses import dataclass, field as dc_field
from pathlib import Path


# ── RBAC ──────────────────────────────────────────────────────────────────────

# Mapping des clés JSON d'entité → noms de méthodes générées dans le contrôleur.
_RBAC_ACTION_TO_METHOD = {
    "index":  "index",
    "show":   "show",
    "create": "new",      # GET form de création
    "store":  "create",   # POST handler de création
    "edit":   "edit",
    "update": "update",
    "delete": "destroy",  # handler de suppression
}


def _with_permission(block: list[str], code: str | None) -> list[str]:
    """Insère @require_permission juste après @staticmethod dans un bloc de méthode."""
    if not code:
        return block
    result: list[str] = []
    for line in block:
        result.append(line)
        if line.rstrip() == "    @staticmethod":
            result.append(f'    @require_permission("{code}")')
    return result


# ── Résultat ──────────────────────────────────────────────────────────────────

@dataclass
class MakeCrudResult:
    created: list[Path] = dc_field(default_factory=list[Path])
    preserved: list[Path] = dc_field(default_factory=list[Path])
    warnings: list[str] = dc_field(default_factory=list[str])
    route_block: str = ""
    dry_run: bool = False


@dataclass(frozen=True)
class CrudManyToOneRelation:
    field_name: str
    field_column: str
    target_entity: str
    target_table: str
    target_pk_column: str
    target_label_column: str
    choices_function: str
    choices_key: str


@dataclass(frozen=True)
class CrudManyToManyRelation:
    source: str
    target: str
    pivot_table: str
    source_key: str
    target_key: str
    target_entity: str
    target_table: str
    target_pk_column: str
    target_label_column: str
    field_name: str
    choices_function: str
    choices_key: str
    selected_function: str
    add_function: str
    sync_function: str
    list_labels_function: str
    show_labels_function: str
    list_context_key: str
    selected_key: str
    show_context_key: str
    order_column: str | None = None
