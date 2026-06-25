"""Smoke test du paquet forge-mvc-testing (TEST-TESTING-PKG-SMOKE-001).

Le 14e paquet (infrastructure de test partagée, dev-only, ADR-041) n'avait
AUCUN test, contrairement aux 13 autres. Ce smoke vérifie qu'il s'importe,
expose son API publique (`FakeRequest`) et que son plugin pytest (point d'entrée
`pytest11`) est importable.

Placé dans `tests/` racine et non dans `packages/forge-mvc-testing/tests/` :
le paquet n'est pas listé dans `testpaths` du pyproject racine (protégé), donc
un test sous son propre dossier ne serait pas collecté.

Décision py.typed (« trancher ») : NON ajouté à ce stade. `forge_mvc_testing`
n'est pas typé strict (~158 erreurs pyright en mode strict, surtout
`fake_request.py` entièrement non annoté) ; ajouter `py.typed` reviendrait à
promettre des types PEP 561 sur un paquet non typé. Cela relève d'un chantier de
typage dédié (comme les 12 opt-ins runtime), différé. Le paquet est dev-only et
n'est jamais une dépendance runtime.
"""
from __future__ import annotations

import importlib

import pytest

mod = pytest.importorskip("forge_mvc_testing")


def test_package_imports_and_exposes_version():
    assert mod.__version__


def test_public_api_fake_request():
    from forge_mvc_testing import FakeRequest

    assert "FakeRequest" in mod.__all__
    req = FakeRequest("POST", "/demo")
    assert req.method == "POST"
    assert req.path == "/demo"


def test_pytest_plugin_module_importable():
    plugin = importlib.import_module("forge_mvc_testing.plugin")
    assert plugin is not None
