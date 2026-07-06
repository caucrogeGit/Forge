"""SKELETON-STANDARDS-CONFORMANCE-001 / T4 (ADR-063) — portail de validation.

`forge new` livre par défaut le point d'entrée unique des gardes qualité : un
workflow CI `.github/workflows/quality.yml` (lint, typage strict, tests,
documentation) et un `Makefile` dont la cible `check` reproduit ces quatre
gardes en une commande locale. L'éditeur, la ligne de commande et la CI
vérifient ainsi exactement la même chose.
"""
from __future__ import annotations

from pathlib import Path

SKELETON = Path(__file__).parent.parent / "skeleton" / "data"

# Les quatre gardes qualité du framework, attendues côté CI comme côté Makefile.
GATES = ("ruff check", "pyright", "pytest", "mkdocs build --strict")


# ── Workflow CI ──────────────────────────────────────────────────────────────

def test_squelette_livre_le_workflow_qualite():
    workflow = SKELETON / ".github" / "workflows" / "quality.yml"
    assert workflow.is_file(), ".github/workflows/quality.yml attendu (ADR-063)"
    content = workflow.read_text(encoding="utf-8")
    for gate in GATES:
        assert gate in content, f"le workflow doit exécuter « {gate} »"


def test_workflow_ne_masque_pas_les_tests():
    # Motif Forge (piège ADR-044) : les gardes non-test sont continue-on-error
    # et un portail final tranche, pour ne jamais masquer l'exécution de pytest.
    content = (SKELETON / ".github" / "workflows" / "quality.yml").read_text(encoding="utf-8")
    assert "continue-on-error" in content


# ── Makefile ─────────────────────────────────────────────────────────────────

def test_squelette_livre_le_makefile():
    makefile = SKELETON / "Makefile"
    assert makefile.is_file(), "Makefile attendu (ADR-063)"
    content = makefile.read_text(encoding="utf-8")
    assert "check:" in content, "cible « check » attendue"
    for gate in GATES:
        assert gate in content, f"make check doit exécuter « {gate} »"


def test_makefile_recettes_indentees_par_tabulation():
    # Une recette make DOIT commencer par une tabulation, jamais des espaces.
    lignes = (SKELETON / "Makefile").read_text(encoding="utf-8").splitlines()
    recettes = [ln for ln in lignes if ln and ln[0] in " \t" and not ln.lstrip().startswith("#")]
    assert recettes, "au moins une recette attendue"
    assert all(ln.startswith("\t") for ln in recettes), "recettes indentées par tabulation"
