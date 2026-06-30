"""Smoke test du paquet forge-mvc-testing (TEST-TESTING-SMOKE-001).

Infrastructure de test partagée, dev-only (ADR-041) : `FakeRequest` et le plugin
pytest (point d'entrée `pytest11`). Ce smoke est co-localisé dans le paquet pour
honorer ADR-040 : exécutable depuis la racine (`testpaths = tests packages`) ET
en autonome (`cd packages/forge-mvc-testing && pytest`). Skip propre si le paquet
n'est pas installé (convention `pytest.importorskip`).
"""
from __future__ import annotations

import importlib
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

MODULE = "forge_mvc_testing"

mod = pytest.importorskip(MODULE)


def test_version_is_non_empty_string() -> None:
    version = getattr(mod, "__version__", None)
    assert isinstance(version, str) and version, f"{MODULE}.__version__ manquant"


def test_public_api_resolves() -> None:
    names = getattr(mod, "__all__", None)
    assert names, f"{MODULE}.__all__ vide ou absent"
    missing = [n for n in names if not hasattr(mod, n)]
    assert not missing, f"{MODULE} : noms de __all__ non résolus : {missing}"


def test_fake_request_instantiable() -> None:
    from forge_mvc_testing import FakeRequest

    assert "FakeRequest" in (mod.__all__ or [])
    req = FakeRequest("POST", "/demo")
    assert req.method == "POST"
    assert req.path == "/demo"


def test_pytest_plugin_module_importable() -> None:
    plugin = importlib.import_module("forge_mvc_testing.plugin")
    assert plugin is not None


def test_ships_py_typed() -> None:
    assert mod.__file__ is not None
    py_typed = Path(mod.__file__).parent / "py.typed"
    assert py_typed.is_file(), f"{MODULE} doit embarquer py.typed (PEP 561)"
