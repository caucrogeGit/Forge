"""Garde-fou SCHEMAS-IN-SYNC-001 : source unique des schémas et copies dérivées.

ADR-058 : `cli/schemas/` est la **source canonique unique** des schémas du cœur
(chargée au runtime, packagée). La copie racine `schemas/` est supprimée.
Les autres présences d'un schéma sont des **copies dérivées**, synchronisées et
gardées par ce test contre toute dérive :

- ``skeleton/data/schemas/`` : gabarit semé dans chaque projet généré par
  ``forge new`` ; ses schémas de base sont byte-identiques au canonique ;
Schémas extraits du cœur vers leur opt-in (absents du cœur, embarqués par le
paquet) : ``rbac`` (ADR-056), ``pivot`` (ADR-057, désormais dans
``forge-mvc-entities`` qui a absorbé pivot, ADR-070). ``forge-mvc-entities``
dépend du cœur : il n'embarque pas de copie des schémas de base (il lit
``cli/schemas`` au runtime), seul ``pivot.schema.json`` lui est propre.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
CLI_SCHEMAS = ROOT / "cli" / "schemas"
ROOT_SCHEMAS = ROOT / "schemas"  # supprimé par ADR-058 : doit rester absent
SKELETON_SCHEMAS = ROOT / "skeleton" / "data" / "schemas"

# Schémas de base du cœur (canonique cli/schemas).
BASE_SCHEMAS = [
    "common.schema.json",
    "entity.schema.json",
    "field.schema.json",
    "relations.schema.json",
]

# Schémas extraits du cœur vers leur opt-in (ADR-056/057).
RBAC_SCHEMA = "rbac.schema.json"
PIVOT_SCHEMA = "pivot.schema.json"
# pivot absorbé par forge-mvc-entities (ADR-070) : pivot.schema.json y est embarqué.
PIVOT_PKG_SCHEMAS = ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities" / "schemas"
RBAC_PKG_SCHEMAS = ROOT / "packages" / "forge-mvc-rbac" / "forge_mvc_rbac" / "schemas"

# Schémas de base copiés dans un opt-in pour son autonomie : doivent rester
# identiques au canonique cli/schemas (anti-dérive, ADR-058). forge-mvc-entities
# embarque common + field aux côtés de pivot.schema.json pour que ses `$ref`
# résolvent de façon autonome (hérité de forge-mvc-pivot, ADR-057/070).
OPTIN_EMBEDDED_BASE: list[tuple[Path, str]] = [
    (PIVOT_PKG_SCHEMAS, "field.schema.json"),
    (PIVOT_PKG_SCHEMAS, "common.schema.json"),
]


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_canonique_existe():
    assert CLI_SCHEMAS.is_dir(), "Le canonique cli/schemas/ doit exister."
    assert SKELETON_SCHEMAS.is_dir(), "Le gabarit skeleton/data/schemas/ doit exister."


def test_pas_de_copie_racine():
    """ADR-058 : la copie redondante schemas/ (racine) est supprimée ; le seul
    canonique est cli/schemas/."""
    assert not ROOT_SCHEMAS.exists(), (
        "schemas/ (racine) doit être supprimé (ADR-058) : cli/schemas/ est la "
        "source canonique unique. Ne pas recréer de copie racine."
    )


@pytest.mark.parametrize("name", BASE_SCHEMAS)
def test_skeleton_base_identique_a_cli(name: str):
    """Les schémas de base du skeleton sont byte-identiques au canonique."""
    cli_f = CLI_SCHEMAS / name
    skel_f = SKELETON_SCHEMAS / name
    assert skel_f.exists(), f"{name} manquant dans skeleton/data/schemas/"
    assert _read(cli_f) == _read(skel_f), (
        f"{name} diffère entre cli/schemas/ et skeleton/data/schemas/. "
        f"Resynchroniser le gabarit (canonique = cli/schemas/)."
    )


@pytest.mark.parametrize("schemas_dir, name", OPTIN_EMBEDDED_BASE)
def test_optin_base_identique_a_cli(schemas_dir: Path, name: str):
    """Un schéma de base embarqué par un opt-in reste identique au canonique."""
    cli_f = CLI_SCHEMAS / name
    pkg_f = schemas_dir / name
    assert pkg_f.exists(), f"{name} manquant dans {schemas_dir}"
    assert _read(cli_f) == _read(pkg_f), (
        f"{name} embarqué par l'opt-in diffère du canonique cli/schemas/. "
        f"Resynchroniser depuis cli/schemas/ (ADR-058)."
    )


def test_rbac_schema_extrait_du_coeur():
    """rbac.schema.json a quitté le cœur (ADR-056) : absent du canonique et du
    gabarit, embarqué par l'opt-in forge-mvc-rbac."""
    for absent_dir in (CLI_SCHEMAS, SKELETON_SCHEMAS):
        assert not (absent_dir / RBAC_SCHEMA).exists(), (
            f"{RBAC_SCHEMA} ne doit plus être dans {absent_dir} (ADR-056)."
        )
    assert (RBAC_PKG_SCHEMAS / RBAC_SCHEMA).exists(), (
        f"{RBAC_SCHEMA} doit être embarqué par forge-mvc-rbac."
    )


def test_pivot_schema_extrait_du_coeur():
    """pivot.schema.json a quitté le cœur (ADR-057) : absent du canonique et du
    gabarit, embarqué par l'opt-in qui porte le pivot (forge-mvc-entities depuis
    l'absorption ADR-070)."""
    for absent_dir in (CLI_SCHEMAS, SKELETON_SCHEMAS):
        assert not (absent_dir / PIVOT_SCHEMA).exists(), (
            f"{PIVOT_SCHEMA} ne doit plus être dans {absent_dir} (ADR-057)."
        )
    assert (PIVOT_PKG_SCHEMAS / PIVOT_SCHEMA).exists(), (
        f"{PIVOT_SCHEMA} doit être embarqué par forge-mvc-entities (ADR-070)."
    )
