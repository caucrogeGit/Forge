# pyright: strict
"""Commande ``forge sessions:init`` — adaptateur mince (CORE-OPTIN-INIT-HELPER-001).

Écrit la migration Sessions dans ``mvc/migrations/`` du projet, sans exécuter
de SQL. Depuis ``OPTIN-DDL-SESSIONS-DB-001``, le SQL n'est plus copié d'un
fichier figé : il est **rendu pour le backend actif** à partir de la
description unique de ``forge_mvc_sessions_db.tables`` (voir
``core.database.table_ddl``). Le fichier produit reste relisible avant
``forge migration:apply``.

Toute la logique (rendu, idempotence, non-écrasement, messages) vit dans
``cli._support.optin_migrations`` (ADR-071) ; ce module ne fournit que le nom
de paquet et le libellé « Sessions ».
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
    "iter_sessions_migration_resources",
    "init_sessions_migrations",
    "main",
]

_PACKAGE = "forge_mvc_sessions_db"
_LABEL = "Sessions"


def iter_sessions_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque ``.sql`` embarqué."""
    return iter_migration_resources(_PACKAGE)


def init_sessions_migrations(project_root: Path) -> int:
    """Copie les migrations Sessions vers ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge sessions:init``."""
    return init_sessions_migrations(Path.cwd())
