"""Tests MODULE-SYSTEM-003 — registre des modules Forge installés."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.modules import (
    MODULE_REGISTRY_FILE,
    ModuleAlreadyInstalledError,
    ModuleInstallResult,
    ModuleRegistryError,
    install_module_manifest,
    is_module_installed,
    load_installed_modules_registry,
    prepare_module_installation,
    save_installed_modules_registry,
    validate_module_manifest,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _manifest(**overrides):
    base = {
        "name": "agenda",
        "label": "Agenda",
        "version": "0.1.0",
        "description": "Module agenda.",
    }
    base.update(overrides)
    return validate_module_manifest(base)


# ---------------------------------------------------------------------------
# Constante MODULE_REGISTRY_FILE
# ---------------------------------------------------------------------------


def test_module_registry_file_est_forge_modules_json():
    assert MODULE_REGISTRY_FILE == "forge_modules.json"


# ---------------------------------------------------------------------------
# load_installed_modules_registry
# ---------------------------------------------------------------------------


def test_registre_absent_retourne_registre_vide(tmp_path):
    registry = load_installed_modules_registry(tmp_path / "absent.json")
    assert registry == {"installed": {}}


def test_registre_valide_charge_correctement(tmp_path):
    data = {"installed": {"agenda": {"name": "agenda", "version": "0.1.0"}}}
    f = tmp_path / "forge_modules.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    registry = load_installed_modules_registry(f)
    assert "agenda" in registry["installed"]


def test_json_invalide_est_refuse(tmp_path):
    f = tmp_path / "forge_modules.json"
    f.write_text("{invalid json", encoding="utf-8")
    with pytest.raises(ModuleRegistryError, match="JSON"):
        load_installed_modules_registry(f)


def test_structure_sans_installed_est_refusee(tmp_path):
    f = tmp_path / "forge_modules.json"
    f.write_text(json.dumps({"modules": {}}), encoding="utf-8")
    with pytest.raises(ModuleRegistryError, match="installed"):
        load_installed_modules_registry(f)


def test_installed_non_dict_est_refuse(tmp_path):
    f = tmp_path / "forge_modules.json"
    f.write_text(json.dumps({"installed": ["agenda"]}), encoding="utf-8")
    with pytest.raises(ModuleRegistryError):
        load_installed_modules_registry(f)


def test_charge_sans_modifier_le_fichier(tmp_path):
    data = {"installed": {"agenda": {"name": "agenda"}}}
    f = tmp_path / "forge_modules.json"
    f.write_text(json.dumps(data), encoding="utf-8")
    before = f.read_text()
    load_installed_modules_registry(f)
    assert f.read_text() == before


# ---------------------------------------------------------------------------
# save_installed_modules_registry
# ---------------------------------------------------------------------------


def test_sauvegarde_json_lisible(tmp_path):
    registry = {"installed": {"agenda": {"name": "agenda"}}}
    f = tmp_path / "forge_modules.json"
    save_installed_modules_registry(registry, f)
    reloaded = json.loads(f.read_text(encoding="utf-8"))
    assert reloaded == registry


def test_sauvegarde_utilise_indentation(tmp_path):
    registry = {"installed": {"agenda": {"name": "agenda"}}}
    f = tmp_path / "forge_modules.json"
    save_installed_modules_registry(registry, f)
    content = f.read_text(encoding="utf-8")
    assert "\n" in content


def test_sauvegarde_puis_rechargement_identique(tmp_path):
    registry = {"installed": {"agenda": {"name": "agenda", "version": "0.1.0"}}}
    f = tmp_path / "forge_modules.json"
    save_installed_modules_registry(registry, f)
    assert load_installed_modules_registry(f) == registry


def test_sauvegarde_sans_ascii_force(tmp_path):
    registry = {"installed": {"agenda": {"label": "Agendá — Módule"}}}
    f = tmp_path / "forge_modules.json"
    save_installed_modules_registry(registry, f)
    content = f.read_text(encoding="utf-8")
    assert "Agendá" in content


# ---------------------------------------------------------------------------
# is_module_installed
# ---------------------------------------------------------------------------


def test_module_absent_retourne_false():
    assert not is_module_installed({"installed": {}}, "agenda")


def test_module_present_retourne_true():
    assert is_module_installed({"installed": {"agenda": {}}}, "agenda")


def test_module_different_retourne_false():
    assert not is_module_installed({"installed": {"agenda": {}}}, "patrimoine")


def test_registre_vide_retourne_false():
    assert not is_module_installed({"installed": {}}, "agenda")


# ---------------------------------------------------------------------------
# prepare_module_installation
# ---------------------------------------------------------------------------


def test_prepare_entree_contient_champs_requis():
    entry = prepare_module_installation(_manifest(), "modules/agenda")
    assert entry["name"] == "agenda"
    assert entry["label"] == "Agenda"
    assert entry["version"] == "0.1.0"
    assert entry["description"] == "Module agenda."
    assert entry["source"] == "modules/agenda"


def test_prepare_url_est_refusee():
    with pytest.raises(ModuleRegistryError, match="URL"):
        prepare_module_installation(_manifest(), "https://example.com/agenda")


def test_prepare_url_ftp_est_refusee():
    with pytest.raises(ModuleRegistryError, match="URL"):
        prepare_module_installation(_manifest(), "ftp://example.com/agenda")


def test_prepare_traversal_est_refuse():
    with pytest.raises(ModuleRegistryError, match="\\.\\."):
        prepare_module_installation(_manifest(), "../modules/agenda")


def test_prepare_traversal_en_sous_chemin_est_refuse():
    with pytest.raises(ModuleRegistryError, match="\\.\\."):
        prepare_module_installation(_manifest(), "modules/../agenda")


def test_prepare_chemin_absolu_hors_projet_refuse(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ModuleRegistryError):
        prepare_module_installation(_manifest(), "/etc/agenda")


def test_prepare_chemin_absolu_dans_projet_relativise(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "modules" / "agenda").mkdir(parents=True)
    entry = prepare_module_installation(_manifest(), tmp_path / "modules" / "agenda")
    assert not Path(entry["source"]).is_absolute()
    assert "modules" in entry["source"]


def test_prepare_provides_stockes_si_presents():
    m = validate_module_manifest({
        "name": "agenda",
        "label": "Agenda",
        "version": "0.1.0",
        "description": "Module agenda.",
        "provides": ["entities", "views"],
    })
    entry = prepare_module_installation(m, "modules/agenda")
    assert "provides" in entry
    assert "entities" in entry["provides"]


def test_prepare_provides_absent_si_vide():
    entry = prepare_module_installation(_manifest(), "modules/agenda")
    assert entry.get("provides", []) == [] or "provides" not in entry


# ---------------------------------------------------------------------------
# install_module_manifest
# ---------------------------------------------------------------------------


def test_install_cree_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(_manifest(), "modules/agenda", registry_path=reg_path)
    assert reg_path.exists()


def test_install_retourne_module_install_result(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    result = install_module_manifest(_manifest(), "modules/agenda", registry_path=reg_path)
    assert isinstance(result, ModuleInstallResult)


def test_install_result_installed_true(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    result = install_module_manifest(_manifest(), "modules/agenda", registry_path=reg_path)
    assert result.installed is True
    assert result.dry_run is False


def test_install_enregistre_dans_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(_manifest(), "modules/agenda", registry_path=reg_path)
    registry = load_installed_modules_registry(reg_path)
    assert "agenda" in registry["installed"]


def test_install_dry_run_ne_cree_pas_fichier(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    result = install_module_manifest(
        _manifest(), "modules/agenda", registry_path=reg_path, dry_run=True
    )
    assert not reg_path.exists()
    assert result.dry_run is True
    assert result.installed is False


def test_install_dry_run_retourne_manifest(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    result = install_module_manifest(
        _manifest(), "modules/agenda", registry_path=reg_path, dry_run=True
    )
    assert result.manifest.name == "agenda"


def test_install_refuse_double_installation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(_manifest(), "modules/agenda", registry_path=reg_path)
    with pytest.raises(ModuleAlreadyInstalledError):
        install_module_manifest(_manifest(), "modules/agenda", registry_path=reg_path)


def test_install_plusieurs_modules_differents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg_path = tmp_path / "forge_modules.json"
    m1 = _manifest(name="agenda", label="Agenda")
    m2 = validate_module_manifest({
        "name": "patrimoine",
        "label": "Patrimoine",
        "version": "0.1.0",
        "description": "Module patrimoine.",
    })
    install_module_manifest(m1, "modules/agenda", registry_path=reg_path)
    install_module_manifest(m2, "modules/patrimoine", registry_path=reg_path)
    registry = load_installed_modules_registry(reg_path)
    assert "agenda" in registry["installed"]
    assert "patrimoine" in registry["installed"]
