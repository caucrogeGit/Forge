"""Smoke test du paquet forge-mvc-mariadb (OPTIN-SMOKE-TESTS-001, ADR-040).

Vérifie qu'une fois installé, le paquet s'importe, expose son API publique,
embarque `py.typed` (PEP 561) et déclare l'entry point de backend BDD attendu
par le cœur (ADR-054). Skip propre si le paquet n'est pas installé.
"""
from __future__ import annotations

from importlib.metadata import entry_points
from pathlib import Path

import pytest

pytestmark = pytest.mark.smoke

MODULE = "forge_mvc_mariadb"

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


def test_backend_respecte_le_contrat() -> None:
    from core.database.backend import DatabaseBackend

    backend = mod.MariaDBBackend()
    assert backend.name == "mariadb"
    assert isinstance(backend, DatabaseBackend)


def test_entry_point_db_backend_declare() -> None:
    eps = entry_points(group="forge_mvc.db_backend")
    names = {ep.name for ep in eps}
    assert "mariadb" in names, (
        "forge-mvc-mariadb doit déclarer l'entry point forge_mvc.db_backend "
        f"nommé 'mariadb' (trouvés : {sorted(names)})."
    )
