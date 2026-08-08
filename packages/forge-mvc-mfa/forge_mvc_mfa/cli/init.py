# pyright: strict
"""Commande ``forge mfa:init`` — adaptateur mince (CORE-OPTIN-INIT-HELPER-001).

Rend la migration du registre anti-rejeu TOTP pour le backend installé et
l'écrit dans ``mvc/migrations/``, sans exécuter de SQL. Toute la logique
(idempotence, non-écrasement, messages) vit dans
``cli._support.optin_migrations`` (ADR-071) ; ce module ne fournit que le nom de
paquet et le libellé.

La commande n'est **pas** un passage obligé de `forge-mvc-mfa`. Elle ne sert
qu'aux projets qui installent ``DbTotpReplayStore`` pour partager le registre
entre plusieurs processus ; le magasin par défaut, en mémoire, n'a besoin
d'aucune table.
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
    "iter_mfa_migration_resources",
    "init_mfa_migrations",
    "main",
]

_PACKAGE = "forge_mvc_mfa"
_LABEL = "MFA"


def iter_mfa_migration_resources() -> Iterator[tuple[str, bytes]]:
    """Itère ``(filename, content_bytes)`` pour chaque migration rendue."""
    return iter_migration_resources(_PACKAGE)


def init_mfa_migrations(project_root: Path) -> int:
    """Écrit les migrations MFA dans ``<project_root>/mvc/migrations/``."""
    return init_optin_migrations(_PACKAGE, _LABEL, project_root)


def main(args: list[str] | None = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge mfa:init``."""
    return init_mfa_migrations(Path.cwd())
