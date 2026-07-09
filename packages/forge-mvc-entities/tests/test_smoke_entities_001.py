"""Smoke test du paquet forge-mvc-entities (ADR-070, ADR-040).

Verifie qu'une fois installe, le paquet s'importe et embarque `py.typed`
(PEP 561). Executable depuis la racine (testpaths) ET en autonome
(`cd packages/forge-mvc-entities && pytest`). Skip propre si le paquet n'est
pas installe (convention `pytest.importorskip` du projet).

Phase 1 (scaffold) : le paquet n'expose pas encore d'API publique ; le test
d'API (`__all__` resout) est ajoute quand le codegen y est deplace (phase 2).
"""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

MODULE = "forge_mvc_entities"

mod = pytest.importorskip(MODULE)


def test_version_is_non_empty_string() -> None:
    version = getattr(mod, "__version__", None)
    assert isinstance(version, str) and version, f"{MODULE}.__version__ manquant"


def test_ships_py_typed() -> None:
    assert mod.__file__ is not None
    py_typed = Path(mod.__file__).parent / "py.typed"
    assert py_typed.is_file(), f"{MODULE} doit embarquer py.typed (PEP 561)"
