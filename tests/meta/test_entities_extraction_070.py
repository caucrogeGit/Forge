"""Garde-fou ADR-070 : le moteur d'entités a quitté le cœur.

Vérifie l'extraction de `cli/entities` vers l'opt-in `forge-mvc-entities` :
absence côté cœur, présence côté paquet, et gating par entry point (les
commandes ne sont plus câblées en dur dans forge.py).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

ROOT = Path(__file__).resolve().parents[2]
PKG = ROOT / "packages" / "forge-mvc-entities" / "forge_mvc_entities"


def test_cli_entities_absent_du_coeur():
    """`cli/entities/` n'existe plus : le moteur d'entités est un opt-in (ADR-070)."""
    assert not (ROOT / "cli" / "entities").exists(), (
        "cli/entities/ doit avoir quitté le cœur (ADR-070) au profit de "
        "packages/forge-mvc-entities/."
    )


def test_forge_mvc_pivot_absent():
    """forge-mvc-pivot est absorbé par forge-mvc-entities (ADR-070), plus de paquet."""
    assert not (ROOT / "packages" / "forge-mvc-pivot").exists(), (
        "packages/forge-mvc-pivot/ doit avoir été absorbé par forge-mvc-entities."
    )


@pytest.mark.parametrize("module", [
    "make_entity.py", "make_relation.py", "make_crud.py", "model.py",
    "migrations.py", "relations.py", "canonical_model_normalizer.py",
    "validation.py", "entity_validate.py", "entity_doc.py",
    "db_apply.py", "db_init.py", "db_config.py", "serverless_db.py",
    "service.py", "make_pivot_crud.py", "commands.py",
])
def test_module_present_dans_le_paquet(module: str):
    assert (PKG / module).is_file(), f"{module} doit vivre dans forge-mvc-entities (ADR-070)."


def test_forge_py_n_importe_pas_le_moteur_au_top_level():
    """forge.py ne dépend pas de forge-mvc-entities au chargement (gating, ADR-070)."""
    src = (ROOT / "forge.py").read_text(encoding="utf-8")
    for line in src.splitlines():
        # Seuls les imports au niveau module (non indentés) créent une dépendance
        # au chargement ; les imports paresseux dans db:init/db:apply (indentés)
        # sont autorisés (échec gracieux si le paquet manque).
        if line[:1].isspace():
            continue
        assert not line.startswith("from forge_mvc_entities"), (
            f"forge.py importe le moteur d'entités au top-level : {line!r}. "
            "Les commandes doivent être gatées (entry point forge_mvc.commands)."
        )
        assert not line.startswith("import forge_mvc_entities"), line


@pytest.mark.parametrize("command", [
    "make:entity", "make:crud", "make:relation", "make:pivot-crud",
    "entity:validate", "entity:doc", "sync:entity", "sync:relations",
    "build:model", "check:model", "migration:make", "db:config",
])
def test_commande_decouverte_par_entry_point(command: str):
    from cli.commands.optin_dispatch import all_optin_commands
    assert command in all_optin_commands(), (
        f"{command} doit être découverte via l'entry point forge_mvc.commands (ADR-070)."
    )
