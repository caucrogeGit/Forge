"""Tests API-ROUTES-LOADER-IMPORT-ERROR-001 — ne pas masquer un import casse.

load_api_routes retournait silencieusement sur tout ModuleNotFoundError. Or si
mvc/api_routes.py EXISTE mais importe un module supprime (media, core.uploads),
l'erreur etait avalee comme « module absent ». On distingue desormais : absent =
silencieux ; import interne casse = ImportError remontee.
"""

import pytest

from core.app import api_routes_loader
from core.app.api_routes_loader import load_api_routes


def test_absent_module_is_silent(monkeypatch):
    def boom(mp):
        raise ModuleNotFoundError(f"No module named '{mp}'", name=mp)

    monkeypatch.setattr(api_routes_loader.importlib, "import_module", boom)
    # Ne doit pas lever : le module api_routes lui-meme est absent.
    load_api_routes(object(), "mvc.api_routes")


def test_absent_parent_package_is_silent(monkeypatch):
    def boom(mp):
        raise ModuleNotFoundError("No module named 'mvc'", name="mvc")

    monkeypatch.setattr(api_routes_loader.importlib, "import_module", boom)
    load_api_routes(object(), "mvc.api_routes")  # parent 'mvc' absent → silencieux


def test_broken_inner_import_raises(monkeypatch):
    # api_routes.py existe mais importe un module supprime → doit remonter.
    def boom(mp):
        raise ModuleNotFoundError("No module named 'media'", name="media")

    monkeypatch.setattr(api_routes_loader.importlib, "import_module", boom)
    with pytest.raises(ImportError):
        load_api_routes(object(), "mvc.api_routes")


def test_other_exception_raises(monkeypatch):
    def boom(mp):
        raise ValueError("boom")

    monkeypatch.setattr(api_routes_loader.importlib, "import_module", boom)
    with pytest.raises(ImportError):
        load_api_routes(object(), "mvc.api_routes")


def test_valid_module_registers_routes(monkeypatch):
    import types as _types

    called = {}
    fake = _types.ModuleType("mvc.api_routes")
    fake.register_api_routes = lambda router: called.setdefault("router", router)
    monkeypatch.setattr(api_routes_loader.importlib, "import_module", lambda mp: fake)

    sentinel = object()
    load_api_routes(sentinel, "mvc.api_routes")
    assert called["router"] is sentinel
