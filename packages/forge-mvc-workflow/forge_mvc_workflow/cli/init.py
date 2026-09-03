# pyright: strict
"""Commande ``forge workflow:init`` — écrit la migration de l'historique.

Adaptateur mince : toute la logique (rendu dialectal, idempotence,
non-écrasement, messages) vit dans ``cli._support.optin_migrations`` (ADR-071).
Ce module ne fournit que le nom de paquet et le libellé.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from cli._support.optin_migrations import (
    STATUS_ERROR,
    STATUS_INFO,
    STATUS_OK,
    STATUS_WARN,
    init_optin_migrations,
    iter_migration_resources,
)

__all__ = [
    "STATUS_OK",
    "STATUS_INFO",
    "STATUS_WARN",
    "STATUS_ERROR",
    "iter_workflow_migration_resources",
    "init_workflow_migrations",
    "main",
]

_PACKAGE = "forge_mvc_workflow"
_LABEL = "Workflow"


def iter_workflow_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque migration rendue."""
    return iter_migration_resources(_PACKAGE)


def init_workflow_migrations(project_root: Path) -> int:
    """Copie la migration de l'historique vers ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: "list[str] | None" = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge workflow:init``."""
    return init_workflow_migrations(Path.cwd())
