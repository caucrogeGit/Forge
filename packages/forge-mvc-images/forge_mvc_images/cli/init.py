# pyright: strict
"""Commande ``forge images:init`` — adaptateur mince (CORE-OPTIN-INIT-HELPER-001).

Copie les migrations SQL embarquées (forge_mvc_images/migrations/) vers
``mvc/migrations/`` du projet, sans exécuter de SQL. Toute la logique
(idempotence, non-écrasement, messages) vit dans
``cli._support.optin_migrations`` (ADR-071) ; ce module ne fournit que le nom
de paquet et le libellé « Images ».
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
    "iter_images_migration_resources",
    "init_images_migrations",
    "main",
]

_PACKAGE = "forge_mvc_images"
_LABEL = "Images"


def iter_images_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque ``.sql`` embarqué."""
    return iter_migration_resources(_PACKAGE)


def init_images_migrations(project_root: Path) -> int:
    """Copie les migrations Images vers ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge images:init``."""
    return init_images_migrations(Path.cwd())
