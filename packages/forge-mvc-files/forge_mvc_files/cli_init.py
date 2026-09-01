# pyright: strict
"""Commande ``forge files:init`` — écrit la migration du registre (ADR-094).

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
    "iter_files_migration_resources",
    "init_files_migrations",
    "main",
]

_PACKAGE = "forge_mvc_files"
_LABEL = "Fichiers"


def iter_files_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque migration rendue."""
    return iter_migration_resources(_PACKAGE)


def init_files_migrations(project_root: Path) -> int:
    """Copie la migration du registre vers ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge files:init``."""
    return init_files_migrations(Path.cwd())
