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
    # Opt-in CLI-only : pas d'API runtime exposée par le package (les commandes
    # sont découvertes via l'entry point, pas via __all__).
    names = getattr(mod, "__all__", None)
    assert names == [], f"{MODULE}.__all__ doit rester vide (CLI-only), vu : {names!r}"


def test_commands_declares_load_with_config() -> None:
    # ADR-074 / ADR-072 : fixtures:load ouvre une connexion BDD -> config: True.
    from forge_mvc_fixtures.commands import COMMANDS

    assert "fixtures:load" in COMMANDS
    spec = COMMANDS["fixtures:load"]
    assert spec["module"] == "forge_mvc_fixtures.cli.load"
    assert spec["config"] is True


def test_ships_py_typed() -> None:
    assert mod.__file__ is not None
    py_typed = Path(mod.__file__).parent / "py.typed"
    assert py_typed.is_file(), f"{MODULE} doit embarquer py.typed (PEP 561)"
