"""Tests MODULE-SYSTEM-003 — flux d'installation déclarative d'un module Forge."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.modules import (
    ModuleAlreadyInstalledError,
    install_module_manifest,
    load_installed_modules_registry,
    validate_module_manifest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_module(root: Path, name: str = "agenda", **overrides) -> Path:
    d = root / name
    d.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name}.",
        **overrides,
    }
    (d / "module.json").write_text(json.dumps(data), encoding="utf-8")
    return d


def _load_manifest(module_dir: Path):
    return validate_module_manifest(
        json.loads((module_dir / "module.json").read_text(encoding="utf-8"))
    )


# ---------------------------------------------------------------------------
# Flux complet
# ---------------------------------------------------------------------------


def test_installation_complete_cree_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    modules = tmp_path / "modules"
    module_dir = _write_module(modules, "agenda")
    manifest = _load_manifest(module_dir)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)
    assert reg_path.exists()
    registry = load_installed_modules_registry(reg_path)
    assert "agenda" in registry["installed"]


def test_installation_enregistre_metadonnees(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    manifest = _load_manifest(module_dir)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)
    registry = load_installed_modules_registry(reg_path)
    entry = registry["installed"]["agenda"]
    assert entry["name"] == "agenda"
    assert entry["version"] == "0.1.0"
    assert entry["source"] == "modules/agenda"


# ---------------------------------------------------------------------------
# Dry-run
# ---------------------------------------------------------------------------


def test_dry_run_naffecte_aucun_fichier(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    manifest = _load_manifest(module_dir)
    reg_path = tmp_path / "forge_modules.json"
    before = set(tmp_path.rglob("*"))
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path, dry_run=True)
    after = set(tmp_path.rglob("*"))
    assert before == after


def test_dry_run_ne_cree_pas_le_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    manifest = _load_manifest(module_dir)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path, dry_run=True)
    assert not reg_path.exists()


# ---------------------------------------------------------------------------
# Aucune copie de fichiers
# ---------------------------------------------------------------------------


def test_aucune_copie_dans_mvc(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    (module_dir / "controllers").mkdir()
    (module_dir / "controllers" / "agenda_controller.py").write_text(
        "# code", encoding="utf-8"
    )
    manifest = _load_manifest(module_dir)
    mvc_dir = tmp_path / "mvc"
    mvc_dir.mkdir()
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)
    assert not (mvc_dir / "agenda_controller.py").exists()
    assert not list(mvc_dir.rglob("agenda_controller.py"))


def test_aucune_modification_routes_py(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    (module_dir / "routes.py").write_text("# module routes", encoding="utf-8")
    manifest = _load_manifest(module_dir)
    mvc_dir = tmp_path / "mvc"
    mvc_dir.mkdir()
    routes_file = mvc_dir / "routes.py"
    routes_file.write_text("# app routes", encoding="utf-8")
    before = routes_file.read_text()
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)
    assert routes_file.read_text() == before


def test_aucune_injection_de_routes_dans_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    manifest = _load_manifest(module_dir)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)
    registry = load_installed_modules_registry(reg_path)
    entry = registry["installed"]["agenda"]
    assert "routes_injected" not in entry
    assert "injected" not in entry


# ---------------------------------------------------------------------------
# Double installation
# ---------------------------------------------------------------------------


def test_double_installation_refusee(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path / "modules", "agenda")
    manifest = _load_manifest(module_dir)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)
    with pytest.raises(ModuleAlreadyInstalledError):
        install_module_manifest(manifest, "modules/agenda", registry_path=reg_path)


# ---------------------------------------------------------------------------
# Plusieurs modules
# ---------------------------------------------------------------------------


def test_plusieurs_modules_installes_sequentiellement(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    for name in ("agenda", "patrimoine"):
        module_dir = _write_module(tmp_path / "modules", name)
        manifest = _load_manifest(module_dir)
        install_module_manifest(manifest, f"modules/{name}", registry_path=reg_path)
    registry = load_installed_modules_registry(reg_path)
    assert "agenda" in registry["installed"]
    assert "patrimoine" in registry["installed"]


# ---------------------------------------------------------------------------
# Audit
# ---------------------------------------------------------------------------


def test_audit_aucun_acces_mvc_dans_registry():
    import core.modules.registry as mod
    source = open(mod.__file__).read()
    assert "mvc/" not in source
    assert "shutil" not in source
    assert "copytree" not in source


def test_audit_aucune_execution_de_code_module():
    import core.modules.registry as mod
    source = open(mod.__file__).read()
    assert "importlib" not in source
    assert "exec(" not in source
    assert "eval(" not in source
    assert "import_module" not in source
