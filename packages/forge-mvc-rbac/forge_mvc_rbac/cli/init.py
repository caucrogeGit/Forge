# pyright: strict
"""Commande ``forge rbac:init`` — adaptateur mince (OPTIN-DDL-RBAC-INIT-001).

Écrit les migrations RBAC (`roles`, `permissions`, `role_permissions`) dans
``mvc/migrations/`` du projet, sans exécuter de SQL. Le DDL est **rendu pour le
backend installé** à partir de la description unique de
``forge_mvc_rbac.tables`` (voir ``core.database.table_ddl``).

Comble un manque : ces trois tables n'avaient aucun chemin d'installation
utilisable depuis un paquet PyPI, alors que ``forge auth:init`` écrit un
``user_roles.sql`` qui les référence.

Toute la logique (rendu, idempotence, non-écrasement, messages) vit dans
``cli._support.optin_migrations`` (ADR-071) ; ce module ne fournit que le nom
de paquet et le libellé « RBAC ».
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
    "iter_rbac_migration_resources",
    "init_rbac_migrations",
    "main",
]

_PACKAGE = "forge_mvc_rbac"
_LABEL = "RBAC"


def iter_rbac_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque migration rendue."""
    return iter_migration_resources(_PACKAGE)


def init_rbac_migrations(project_root: Path) -> int:
    """Écrit les migrations RBAC dans ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge rbac:init``."""
    return init_rbac_migrations(Path.cwd())
