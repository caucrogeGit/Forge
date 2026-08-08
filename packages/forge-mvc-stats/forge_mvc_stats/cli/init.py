# pyright: strict
"""Commande ``forge stats:init`` — adaptateur mince (CORE-OPTIN-INIT-HELPER-001).

Rend la migration de `forge_stats_events` pour le backend installé et l'écrit
dans ``mvc/migrations/``, sans exécuter de SQL. Toute la logique (idempotence,
non-écrasement, messages) vit dans ``cli._support.optin_migrations`` (ADR-071) ;
ce module ne fournit que le nom de paquet et le libellé.

Ce paquet était en retrait des autres opt-ins adossés à la base : il décrivait
bien sa table, mais n'avait ni ``MIGRATIONS``, ni commande d'amorçage, si bien
que ``forge_stats_events`` n'était créée par aucune commande Forge et que sa
documentation affirmait à tort que l'opt-in n'apportait aucune table
(`STATS-OPTIN-CONFORM-001`).
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
    "iter_stats_migration_resources",
    "init_stats_migrations",
    "main",
]

_PACKAGE = "forge_mvc_stats"
_LABEL = "Stats"


def iter_stats_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque migration rendue."""
    return iter_migration_resources(_PACKAGE)


def init_stats_migrations(project_root: Path) -> int:
    """Écrit les migrations Stats dans ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge stats:init``."""
    return init_stats_migrations(Path.cwd())
