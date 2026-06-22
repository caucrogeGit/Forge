"""Garde-fou SCHEMAS-IN-SYNC-001 : synchronisation des trois copies de schémas.

Forge maintient trois jeux de schémas JSON, pour trois contextes distincts :

- ``cli/schemas/`` : source **canonique** utilisée par l'outil
  (``schema:list``, ``schema:doctor``, ``entity:validate``). Inclut ``rbac``.
- ``schemas/`` (racine du dépôt) : copie « projet » du dépôt lui-même
  (dogfooding), pour la résolution ``$schema`` / l'autocomplétion VS Code sur
  ses propres fichiers d'entités. Doit être **identique** à ``cli/schemas/``.
- ``cli/skeleton/data/schemas/`` : gabarit copié dans chaque projet généré par
  ``forge new``. Reprend les schémas de base **byte-identiques**, mais **omet
  volontairement** ``rbac`` (opt-in) et son entrée dans l'index.

Ces copies sont recopiées à la main : ce test détecte toute dérive.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
CLI_SCHEMAS = ROOT / "cli" / "schemas"
PROJECT_SCHEMAS = ROOT / "schemas"
SKELETON_SCHEMAS = ROOT / "cli" / "skeleton" / "data" / "schemas"

# Schémas de base partagés par les trois copies (byte-identiques partout).
BASE_SCHEMAS = [
    "common.schema.json",
    "entity.schema.json",
    "field.schema.json",
    "pivot.schema.json",
    "relations.schema.json",
]
# Différences volontaires côté skeleton (projet de base sans opt-in RBAC).
SKELETON_OMITS = {"rbac.schema.json"}


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def test_dossiers_existent():
    for d in (CLI_SCHEMAS, PROJECT_SCHEMAS, SKELETON_SCHEMAS):
        assert d.is_dir(), f"Dossier de schémas absent : {d}"


def test_racine_identique_a_cli_schemas():
    """schemas/ (racine) doit être une copie intégrale et identique de cli/schemas/."""
    cli_files = {p.name for p in CLI_SCHEMAS.glob("*.json")}
    root_files = {p.name for p in PROJECT_SCHEMAS.glob("*.json")}
    assert cli_files == root_files, (
        f"schemas/ (racine) et cli/schemas/ n'ont pas les mêmes fichiers : "
        f"seulement cli={cli_files - root_files}, seulement racine={root_files - cli_files}"
    )
    drift = [n for n in cli_files if _read(CLI_SCHEMAS / n) != _read(PROJECT_SCHEMAS / n)]
    assert not drift, (
        f"Dérive entre cli/schemas/ et schemas/ (racine) : {drift}. "
        f"Resynchroniser (copie intégrale identique attendue)."
    )


@pytest.mark.parametrize("name", BASE_SCHEMAS)
def test_skeleton_base_identique_a_cli(name: str):
    """Les schémas de base du skeleton sont byte-identiques à cli/schemas/."""
    cli_f = CLI_SCHEMAS / name
    skel_f = SKELETON_SCHEMAS / name
    assert skel_f.exists(), f"{name} manquant dans cli/skeleton/data/schemas/"
    assert _read(cli_f) == _read(skel_f), (
        f"{name} diffère entre cli/schemas/ et cli/skeleton/data/schemas/. "
        f"Resynchroniser le gabarit."
    )


def test_skeleton_omet_bien_rbac():
    """Le skeleton omet volontairement rbac (opt-in, hors squelette de base)."""
    for omitted in SKELETON_OMITS:
        assert not (SKELETON_SCHEMAS / omitted).exists(), (
            f"{omitted} ne doit pas être dans le squelette de base (opt-in) : "
            f"différence volontaire vs cli/schemas/."
        )
        assert (CLI_SCHEMAS / omitted).exists(), (
            f"{omitted} doit exister dans cli/schemas/ (source canonique)."
        )
