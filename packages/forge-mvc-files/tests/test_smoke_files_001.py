"""Smoke test du paquet forge-mvc-files (OPTIN-SMOKE-TESTS-001).

Vérifie qu'une fois installé, le paquet s'importe, expose son API publique
et embarque `py.typed` (PEP 561). Exécutable depuis la racine (testpaths)
ET en autonome (`cd packages/forge-mvc-files && pytest`). Skip propre si le paquet n'est pas
installé (convention `pytest.importorskip` du projet).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

MODULE = "forge_mvc_files"

mod = pytest.importorskip(MODULE)


def test_version_is_non_empty_string() -> None:
    version = getattr(mod, "__version__", None)
    assert isinstance(version, str) and version, f"{MODULE}.__version__ manquant"


def test_public_api_resolves() -> None:
    names = getattr(mod, "__all__", None)
    assert names, f"{MODULE}.__all__ vide ou absent"
    missing = [n for n in names if not hasattr(mod, n)]
    assert not missing, f"{MODULE} : noms de __all__ non résolus : {missing}"


def test_ships_py_typed() -> None:
    assert mod.__file__ is not None
    py_typed = Path(mod.__file__).parent / "py.typed"
    assert py_typed.is_file(), f"{MODULE} doit embarquer py.typed (PEP 561)"
