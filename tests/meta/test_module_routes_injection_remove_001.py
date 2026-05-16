"""Garde-fou méta MODULE-ROUTES-INJECTION-REMOVE-001.

Vérifie que l'injection automatique de routes dans les fichiers applicatifs
n'est plus possible depuis l'API publique des modules Forge.

- prepare_module_route_injection n'existe plus dans core.modules
- les helpers d'injection (_build_injection_block, _module_marker) sont supprimés
- MODULE_ROUTES_FILE n'est plus dans l'API publique
- le mécanisme explicite generate_module_routes existe toujours
- module:install ne déclenche aucune écriture dans mvc/routes.py
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

import core.modules
import core.modules.routes as _routes_module

pytestmark = pytest.mark.meta

PROJECT_ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# Symboles d'injection supprimés de l'API publique
# ---------------------------------------------------------------------------

def test_prepare_module_route_injection_removed_from_public_api():
    """prepare_module_route_injection ne doit plus exister dans core.modules."""
    assert not hasattr(core.modules, "prepare_module_route_injection"), (
        "prepare_module_route_injection a été supprimé — "
        "utiliser generate_module_routes pour le mécanisme explicite"
    )


def test_module_route_injection_result_removed_from_public_api():
    """ModuleRouteInjectionResult ne doit plus être exporté."""
    assert not hasattr(core.modules, "ModuleRouteInjectionResult"), (
        "ModuleRouteInjectionResult correspondait à l'ancienne injection "
        "automatique — supprimé avec prepare_module_route_injection"
    )


def test_module_routes_already_injected_error_removed_from_public_api():
    """ModuleRoutesAlreadyInjectedError ne doit plus être exportée."""
    assert not hasattr(core.modules, "ModuleRoutesAlreadyInjectedError"), (
        "ModuleRoutesAlreadyInjectedError correspondait à l'ancienne injection "
        "automatique — supprimé avec prepare_module_route_injection"
    )


def test_module_routes_file_not_in_public_api():
    """MODULE_ROUTES_FILE ne doit plus être dans l'API publique de core.modules."""
    assert not hasattr(core.modules, "MODULE_ROUTES_FILE"), (
        "MODULE_ROUTES_FILE était lié à l'ancien fichier cible d'injection "
        "(mvc/module_routes.py) — retiré de l'API publique"
    )


# ---------------------------------------------------------------------------
# Helpers d'injection supprimés du module interne
# ---------------------------------------------------------------------------

def test_build_injection_block_removed_from_routes_module():
    """_build_injection_block ne doit plus exister dans core.modules.routes."""
    assert not hasattr(_routes_module, "_build_injection_block"), (
        "_build_injection_block généraient les blocs d'injection avec marqueurs — "
        "supprimé : Forge ne construit plus de blocs d'injection"
    )


def test_module_marker_removed_from_routes_module():
    """_module_marker ne doit plus exister dans core.modules.routes."""
    assert not hasattr(_routes_module, "_module_marker"), (
        "_module_marker générait les marqueurs forge-module-routes:name:start/end — "
        "supprimé : les marqueurs d'injection ne sont plus générés"
    )


# ---------------------------------------------------------------------------
# Mécanisme explicite toujours disponible
# ---------------------------------------------------------------------------

def test_generate_module_routes_still_exists():
    """generate_module_routes doit toujours être accessible dans core.modules."""
    assert hasattr(core.modules, "generate_module_routes")
    assert callable(core.modules.generate_module_routes)


def test_module_route_generation_result_still_exported():
    """ModuleRouteGenerationResult doit toujours être exporté."""
    assert hasattr(core.modules, "ModuleRouteGenerationResult")


# ---------------------------------------------------------------------------
# module:install ne modifie pas mvc/routes.py
# ---------------------------------------------------------------------------

def test_module_install_does_not_write_mvc_routes(tmp_path, monkeypatch):
    """module:install ne doit pas écrire dans mvc/routes.py."""
    monkeypatch.chdir(tmp_path)
    from core.modules import install_module_manifest, load_module_manifest

    module_dir = tmp_path / "modules" / "test_mod"
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.json").write_text(
        json.dumps({
            "name": "test_mod",
            "label": "Test",
            "version": "0.1.0",
            "description": "Module test.",
            "provides": ["routes"],
            "paths": {"routes": "routes.py"},
        }),
        encoding="utf-8",
    )
    (module_dir / "routes.py").write_text("def register_routes(router): pass\n", encoding="utf-8")

    app_routes = tmp_path / "mvc" / "routes.py"
    app_routes.parent.mkdir(parents=True, exist_ok=True)
    original = "from core.http.router import Router\nrouter = Router()\n"
    app_routes.write_text(original, encoding="utf-8")

    manifest = load_module_manifest(module_dir / "module.json")
    install_module_manifest(manifest, "modules/test_mod", registry_path=tmp_path / "forge_modules.json")

    assert app_routes.read_text(encoding="utf-8") == original, (
        "module:install ne doit pas modifier mvc/routes.py"
    )


# ---------------------------------------------------------------------------
# Pas de pattern d'injection dans le code source de production
# ---------------------------------------------------------------------------

def test_no_injection_code_in_routes_source():
    """core/modules/routes.py ne doit pas contenir la fonction d'injection supprimée."""
    src = (PROJECT_ROOT / "core" / "modules" / "routes.py").read_text(encoding="utf-8")
    assert "prepare_module_route_injection" not in src, (
        "prepare_module_route_injection ne doit plus exister dans core/modules/routes.py"
    )
    assert "_build_injection_block" not in src, (
        "_build_injection_block ne doit plus exister dans core/modules/routes.py"
    )
    assert "_module_marker" not in src, (
        "_module_marker ne doit plus exister dans core/modules/routes.py"
    )
