# pyright: strict
"""Commande ``forge opt-in:installed`` — opt-ins réellement installés (pip).

Lecture seule, **sans contexte projet** : interroge les distributions installées
(``importlib.metadata``) pour chaque opt-in officiel et backend BDD du catalogue.

Complémentaire de ``opt-in:list`` : ``opt-in:list`` dit ce qui est **câblé dans
le projet** (couche ``optins/``), ``opt-in:installed`` dit ce qui est **installé**
dans l'environnement Python. Les opt-ins CLI-only (deploy, fixtures) s'utilisent
dès qu'ils sont installés, sans câblage projet : c'est cette commande qui fait foi
pour eux.
"""
from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from cli.optins.catalog import (
    CATEGORY_DATABASE,
    CATEGORY_LABELS,
    DB_BACKENDS,
    optins_by_category,
)

__all__ = ["installed_version", "list_installed", "main"]


def installed_version(dist: str) -> "str | None":
    """Version installée de la distribution, ou ``None`` si absente."""
    try:
        return version(dist)
    except PackageNotFoundError:
        return None


def _print_row(name: str, dist: str) -> bool:
    found = installed_version(dist)
    status = found if found else "(non installé)"
    print(f"  {name:<15} {dist:<24} {status}")
    return found is not None


def list_installed() -> int:
    """Affiche les opt-ins et backends installés (pip). Toujours ``0``."""
    print("Opt-ins installés (pip)")
    print("")
    installed_count = 0
    for category, opts in optins_by_category().items():
        print(CATEGORY_LABELS[category])
        for opt in opts:
            if _print_row(opt.name, opt.package_dist):
                installed_count += 1
        print("")

    print(CATEGORY_LABELS[CATEGORY_DATABASE])
    print("            un seul backend par projet (famille exclusive)")
    for backend in DB_BACKENDS:
        if _print_row(backend.name, backend.package_dist):
            installed_count += 1
    print("")

    if installed_count == 0:
        print("Aucun opt-in installé. Installez-en un : forge opt-in:install <name>.")
    else:
        print(f"{installed_count} opt-in(s) installé(s). Câblage projet : forge opt-in:list.")
    return 0


def main(argv: "list[str] | None" = None) -> int:
    """Point d'entrée appelé par ``forge.py`` pour ``forge opt-in:installed``."""
    return list_installed()
