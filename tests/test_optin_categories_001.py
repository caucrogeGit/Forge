"""Garde-fou ADR-OPTIN-CATEGORIES-001 (ADR-055).

Le catalogue des opt-ins porte une destination fonctionnelle (`category`),
distincte du `kind` technique. Chaque opt-in déclare une catégorie de la liste
canonique, le regroupement couvre tout le catalogue, et les backends BDD vivent
dans un registre séparé (famille exclusive, ADR-054).
"""
from __future__ import annotations

from pathlib import Path

from cli.optins.catalog import (
    CATEGORY_LABELS,
    CATEGORY_ORDER,
    DB_BACKENDS,
    OFFICIAL_OPTINS,
    optins_by_category,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Paquets `forge-mvc-*` qui ne sont pas des opt-ins d'application :
# - les backends BDD (famille exclusive, registre DB_BACKENDS, ADR-054) ;
# - forge-mvc-testing : infrastructure de test dev-only (ADR-041).
_DB_BACKEND_NAMES = {b.name for b in DB_BACKENDS}
_NON_APP_PACKAGES = _DB_BACKEND_NAMES | {"testing"}


def test_chaque_optin_a_une_categorie_canonique():
    offenders = [
        opt.name for opt in OFFICIAL_OPTINS.values()
        if opt.category not in CATEGORY_LABELS
    ]
    assert not offenders, (
        f"opt-ins sans catégorie canonique (voir ADR-055) : {offenders}"
    )


def test_regroupement_couvre_tout_le_catalogue():
    grouped = optins_by_category()
    regroupes = [opt.name for opts in grouped.values() for opt in opts]
    assert sorted(regroupes) == sorted(OFFICIAL_OPTINS)


def test_regroupement_suit_l_ordre_canonique():
    grouped = optins_by_category()
    assert list(grouped) == [c for c in CATEGORY_ORDER if c in grouped]


def test_backends_bdd_hors_official_optins():
    # Les backends sont exclusifs (un seul par projet) : ils ne s'« enable » pas
    # comme les autres opt-ins et ne figurent pas dans OFFICIAL_OPTINS.
    assert _DB_BACKEND_NAMES == {"mariadb", "sqlite", "postgres", "mssql"}
    assert _DB_BACKEND_NAMES.isdisjoint(OFFICIAL_OPTINS)


def test_catalogue_couvre_les_paquets_dapplication():
    """Tout paquet forge-mvc-* est soit un opt-in catalogué, soit un backend BDD,
    soit explicitement hors périmètre (testing). Empêche d'oublier de classer un
    nouveau paquet (ADR-055)."""
    packages = {
        p.name[len("forge-mvc-"):]
        for p in (PROJECT_ROOT / "packages").iterdir()
        if p.is_dir() and p.name.startswith("forge-mvc-")
    }
    classes = set(OFFICIAL_OPTINS) | _NON_APP_PACKAGES
    non_classes = packages - classes
    assert not non_classes, (
        f"paquets forge-mvc-* non classés (catalogue ou exclusion explicite) : "
        f"{sorted(non_classes)}"
    )
