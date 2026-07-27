"""Smoke test du paquet forge-mvc-audit (OPTIN-SMOKE-TESTS-001)."""
from __future__ import annotations

from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

MODULE = "forge_mvc_audit"

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


def test_declares_its_table() -> None:
    """Le .sql fige est remplace par une declaration rendue par le dialecte
    (OPTIN-DDL-DIALECTAL) : le paquet declare, il n'embarque plus de SQL."""
    assert mod.__file__ is not None
    assert not (Path(mod.__file__).parent / "migrations").exists()
    tables = __import__("forge_mvc_audit.tables", fromlist=["tables"])
    assert tables.MIGRATIONS, f"{MODULE} doit declarer ses migrations"
