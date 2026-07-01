# pyright: strict
"""Garde-fou CLI-COMPLEXITY-BUDGET-001 : budget de complexité du lanceur CLI.

`forge.py` a été ramené à un lanceur mince (ADR-059) : il doit le rester. Ce
garde-fou pose, avec la seule bibliothèque standard (AST, pas de dépendance
`radon`) :

- un plafond de taille total pour `forge.py` (cliquet : on ne fait que le
  baisser quand le fichier maigrit, jamais le monter) ;
- une longueur maximale pour `main()`, le point de dispatch central ;
- une longueur maximale pour toute autre fonction.

But : empêcher le retour d'un gros dispatcher central (chaîne `if/elif`) dans le
cœur, alors que le dispatch est désormais table + entry points.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).resolve().parents[2]
FORGE_PY = PROJECT_ROOT / "forge.py"

# Cliquet : forge.py ne doit pas dépasser ce plafond. Baisser cette valeur quand
# forge.py maigrit ; ne jamais la monter sans justification (le dispatch des
# commandes ne revient pas dans le cœur, cf. ADR-059).
_FORGE_PY_MAX_LINES = 780

# main() est le point de dispatch central : commandes natives + interception
# --help + appels dispatch_core/dispatch_optin. Borné à part.
_MAIN_MAX_LINES = 140

# Toute autre fonction reste courte (une responsabilité).
_MAX_FUNCTION_LINES = 90
_LENGTH_EXCEPTIONS = {"main"}


def _function_lengths() -> list[tuple[str, int]]:
    tree = ast.parse(FORGE_PY.read_text(encoding="utf-8"))
    lengths: list[tuple[str, int]] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = node.end_lineno or node.lineno
            lengths.append((node.name, end - node.lineno + 1))
    return lengths


def test_forge_py_reste_mince():
    lines = len(FORGE_PY.read_text(encoding="utf-8").splitlines())
    assert lines <= _FORGE_PY_MAX_LINES, (
        f"forge.py fait {lines} lignes (plafond {_FORGE_PY_MAX_LINES}). "
        "forge.py est un lanceur mince (ADR-059) : le dispatch des commandes "
        "passe par les tables (CORE_COMMANDS) et les entry points, pas par une "
        "chaîne if/elif dans le cœur."
    )


def test_main_reste_borne():
    main_lengths = [n for name, n in _function_lengths() if name == "main"]
    assert main_lengths, "forge.py doit définir main()."
    longest = max(main_lengths)
    assert longest <= _MAIN_MAX_LINES, (
        f"main() fait {longest} lignes (plafond {_MAIN_MAX_LINES}). "
        "Extraire les commandes vers CORE_COMMANDS ou les entry points plutôt "
        "que de rallonger le dispatcher central."
    )


def test_aucune_autre_fonction_trop_longue():
    offenders = [
        f"{name} ({n} lignes)"
        for name, n in _function_lengths()
        if name not in _LENGTH_EXCEPTIONS and n > _MAX_FUNCTION_LINES
    ]
    assert not offenders, (
        "Fonctions trop longues dans forge.py (plafond "
        f"{_MAX_FUNCTION_LINES} lignes) : " + ", ".join(sorted(offenders)) + ". "
        "Découper en fonctions à responsabilité unique."
    )
