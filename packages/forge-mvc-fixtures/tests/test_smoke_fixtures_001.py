"""Smoke test du paquet forge-mvc-fixtures (OPTIN-SMOKE-TESTS-001, ADR-040).

Vérifie qu'une fois installé, le paquet s'importe, expose une version et embarque
`py.typed` (PEP 561). Opt-in CLI-only au scaffold (ADR-074) : pas de migration ni
d'API runtime, et la table de commandes est encore vide. Skip propre si le paquet
n'est pas installé.
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

MODULE = "forge_mvc_fixtures"

mod = pytest.importorskip(MODULE)


def test_version_is_non_empty_string() -> None:
    version = getattr(mod, "__version__", None)
    assert isinstance(version, str) and version, f"{MODULE}.__version__ manquant"


def test_all_is_defined() -> None:
    # Scaffold : __all__ existe et est vide (aucune API publique livrée encore).
    names = getattr(mod, "__all__", None)
    assert names == [], f"{MODULE}.__all__ doit être vide au scaffold, vu : {names!r}"


def test_commands_table_is_empty_dict() -> None:
    # ADR-074 : la plomberie de l'entry point est en place, commandes à venir.
    from forge_mvc_fixtures.commands import COMMANDS

    assert COMMANDS == {}, f"COMMANDS doit être vide au scaffold, vu : {COMMANDS!r}"


def test_ships_py_typed() -> None:
    assert mod.__file__ is not None
    py_typed = Path(mod.__file__).parent / "py.typed"
    assert py_typed.is_file(), f"{MODULE} doit embarquer py.typed (PEP 561)"
