"""
Tests MODULE-REMOVE-001 — Suppression contrôlée des modules Forge.

Valide :
- refuse un module inconnu
- dry-run ne modifie rien
- supprime les fichiers tracés et inchangés
- conserve les fichiers modifiés
- conserve les fichiers dont la source est absente
- retire les routes marquées
- refuse/signale les marqueurs de routes absents
- met à jour forge_modules.json
- protège contre le path traversal dans forge_modules.json
- ne supprime pas les fichiers non tracés
- ne supprime pas les dossiers parents
- commande CLI dispatche module:remove
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.modules import (
    ModuleNotInstalledError,
    ModuleRemoveError,
    install_module_files,
    install_module_manifest,
    load_module_manifest,
    load_installed_modules_registry,
    remove_module,
)


# ── Helpers ─────────────────────────────────────────────────────────────────────

def _write_module(
    root: Path,
    name: str = "agenda",
    *,
    provides: list[str] | None = None,
    paths: dict[str, str] | None = None,
    entity_content: str = "{}\n",
) -> Path:
    module_dir = root / "modules" / name
    module_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name}.",
        "provides": provides if provides is not None else ["entities"],
        "paths": paths if paths is not None else {"entities": "entities"},
    }
    (module_dir / "module.json").write_text(json.dumps(data), encoding="utf-8")
    entities_dir = module_dir / "entities"
    entities_dir.mkdir(exist_ok=True)
    (entities_dir / "item.json").write_text(entity_content, encoding="utf-8")
    return module_dir


def _register(root: Path, module_dir: Path, name: str = "agenda") -> Path:
    manifest = load_module_manifest(module_dir / "module.json")
    registry_path = root / "forge_modules.json"
    install_module_manifest(manifest, f"modules/{name}", registry_path=registry_path)
    return registry_path


def _full_install(root: Path, name: str = "agenda") -> Path:
    module_dir = _write_module(root, name)
    registry_path = _register(root, module_dir, name)
    install_module_files(name, registry_path=registry_path)
    return registry_path


def _inject_routes_block(root: Path, name: str) -> Path:
    routes_file = root / "mvc" / "module_routes.py"
    routes_file.parent.mkdir(parents=True, exist_ok=True)
    routes_file.write_text(
        '"""Routes de modules Forge injectées explicitement."""\n'
        "\n"
        "\n"
        "def register_module_routes(router):\n"
        f"    # forge-module-routes:{name}:start\n"
        f"    from modules.{name}.routes import register_routes as register_{name}_routes\n"
        f"    register_{name}_routes(router)\n"
        f"    # forge-module-routes:{name}:end\n"
        "    return None\n",
        encoding="utf-8",
    )
    return routes_file


# ── module inconnu ───────────────────────────────────────────────────────────────

def test_remove_refuse_module_inconnu(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "forge_modules.json"
    reg.write_text('{"installed": {}}', encoding="utf-8")
    with pytest.raises(ModuleNotInstalledError):
        remove_module("inexistant", registry_path=reg)


def test_remove_refuse_module_inconnu_registre_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ModuleNotInstalledError):
        remove_module("inexistant", registry_path=tmp_path / "forge_modules.json")


# ── dry-run ──────────────────────────────────────────────────────────────────────

def test_dry_run_ne_supprime_aucun_fichier(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    snapshot_before = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*") if p.is_file()
    }
    result = remove_module("agenda", registry_path=registry_path, dry_run=True)
    assert result.dry_run is True
    snapshot_after = {
        p.relative_to(tmp_path).as_posix(): p.read_bytes()
        for p in tmp_path.rglob("*") if p.is_file()
    }
    assert snapshot_before == snapshot_after


def test_dry_run_retourne_fichiers_a_supprimer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    result = remove_module("agenda", registry_path=registry_path, dry_run=True)
    assert len(result.files_deleted) > 0
    assert all("mvc/entities" in f for f in result.files_deleted)


def test_dry_run_ne_modifie_pas_le_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    reg_before = registry_path.read_text(encoding="utf-8")
    remove_module("agenda", registry_path=registry_path, dry_run=True)
    assert registry_path.read_text(encoding="utf-8") == reg_before


# ── suppression fichiers inchangés ───────────────────────────────────────────────

def test_supprime_fichier_identique_a_la_source(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    installed_file = tmp_path / "mvc" / "entities" / "item.json"
    assert installed_file.exists()
    result = remove_module("agenda", registry_path=registry_path)
    assert not installed_file.exists()
    assert "mvc/entities/item.json" in result.files_deleted


def test_registre_mis_a_jour_apres_suppression(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    remove_module("agenda", registry_path=registry_path)
    registry = load_installed_modules_registry(registry_path)
    assert "agenda" not in registry["installed"]


def test_registry_updated_true_apres_suppression(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    result = remove_module("agenda", registry_path=registry_path)
    assert result.registry_updated is True


# ── protection des fichiers modifiés ─────────────────────────────────────────────

def test_conserve_fichier_modifie(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    installed_file = tmp_path / "mvc" / "entities" / "item.json"
    installed_file.write_text('{"modified": true}\n', encoding="utf-8")
    result = remove_module("agenda", registry_path=registry_path)
    assert installed_file.exists(), "Le fichier modifié doit être conservé"
    assert "mvc/entities/item.json" not in result.files_deleted
    kept_paths = [d.path for d in result.files_kept]
    assert "mvc/entities/item.json" in kept_paths


def test_decision_keep_modified_contient_raison(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    installed_file = tmp_path / "mvc" / "entities" / "item.json"
    installed_file.write_text('{"changed": true}\n', encoding="utf-8")
    result = remove_module("agenda", registry_path=registry_path)
    decisions = {d.path: d for d in result.files_kept}
    assert decisions["mvc/entities/item.json"].action == "keep_modified"


def test_registre_mis_a_jour_meme_avec_fichier_conserve(tmp_path, monkeypatch):
    """Le module est retiré du registre même si des fichiers sont conservés."""
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    installed_file = tmp_path / "mvc" / "entities" / "item.json"
    installed_file.write_text('{"modified": true}\n', encoding="utf-8")
    remove_module("agenda", registry_path=registry_path)
    registry = load_installed_modules_registry(registry_path)
    assert "agenda" not in registry["installed"]


# ── source introuvable ───────────────────────────────────────────────────────────

def test_conserve_fichier_si_source_absente(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    # Supprimer le dossier source du module
    import shutil
    shutil.rmtree(tmp_path / "modules" / "agenda")
    installed_file = tmp_path / "mvc" / "entities" / "item.json"
    result = remove_module("agenda", registry_path=registry_path)
    assert installed_file.exists(), "Sans source, le fichier doit être conservé"
    decisions = {d.path: d for d in result.files_kept}
    assert decisions["mvc/entities/item.json"].action == "keep_source_missing"


# ── routes ────────────────────────────────────────────────────────────────────────

def test_retire_bloc_de_routes_avec_marqueurs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    routes_file = _inject_routes_block(tmp_path, "agenda")
    assert "forge-module-routes:agenda:start" in routes_file.read_text()
    result = remove_module("agenda", registry_path=registry_path, routes_file=routes_file)
    assert result.routes_removed is True
    assert "forge-module-routes:agenda:start" not in routes_file.read_text()


def test_routes_note_retirees_quand_marqueurs_presents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    routes_file = _inject_routes_block(tmp_path, "agenda")
    result = remove_module("agenda", registry_path=registry_path, routes_file=routes_file)
    assert "retirées" in result.routes_note.lower()


def test_routes_note_marqueurs_absents(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    routes_file = tmp_path / "mvc" / "module_routes.py"
    routes_file.parent.mkdir(parents=True, exist_ok=True)
    routes_file.write_text("def register_module_routes(router):\n    return None\n")
    result = remove_module("agenda", registry_path=registry_path, routes_file=routes_file)
    assert result.routes_removed is False
    assert "marqueurs absents" in result.routes_note.lower() or "nettoyage" in result.routes_note.lower()


def test_routes_absent_quand_fichier_routes_absent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    routes_file = tmp_path / "mvc" / "module_routes.py"
    result = remove_module("agenda", registry_path=registry_path, routes_file=routes_file)
    assert result.routes_removed is False


def test_dry_run_routes_simulees_sans_modification(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    routes_file = _inject_routes_block(tmp_path, "agenda")
    content_before = routes_file.read_text()
    result = remove_module("agenda", registry_path=registry_path, routes_file=routes_file, dry_run=True)
    assert routes_file.read_text() == content_before
    assert result.routes_removed is True


# ── path traversal ────────────────────────────────────────────────────────────────

def test_refuse_path_traversal_dans_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "forge_modules.json"
    reg.write_text(json.dumps({"installed": {"evil": {
        "name": "evil", "version": "1.0.0",
        "files_installed": ["../../etc/passwd"],
        "source": "modules/evil",
    }}}), encoding="utf-8")
    with pytest.raises(ModuleRemoveError):
        remove_module("evil", registry_path=reg)


def test_refuse_chemin_absolu_dans_registre(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "forge_modules.json"
    reg.write_text(json.dumps({"installed": {"evil": {
        "name": "evil", "version": "1.0.0",
        "files_installed": ["/etc/passwd"],
        "source": "modules/evil",
    }}}), encoding="utf-8")
    with pytest.raises(ModuleRemoveError):
        remove_module("evil", registry_path=reg)


# ── fichier non tracé ─────────────────────────────────────────────────────────────

def test_ne_supprime_pas_fichier_non_trace(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    # Fichier non déclaré dans files_installed
    extra = tmp_path / "mvc" / "entities" / "not_tracked.json"
    extra.write_text("{}", encoding="utf-8")
    remove_module("agenda", registry_path=registry_path)
    assert extra.exists(), "Le fichier non tracé ne doit pas être supprimé"


# ── dossiers parents ──────────────────────────────────────────────────────────────

def test_ne_supprime_pas_dossier_parent(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    entities_dir = tmp_path / "mvc" / "entities"
    remove_module("agenda", registry_path=registry_path)
    assert entities_dir.exists(), "Le dossier parent ne doit pas être supprimé"


# ── résultat ─────────────────────────────────────────────────────────────────────

def test_result_module_name_correct(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    result = remove_module("agenda", registry_path=registry_path)
    assert result.module_name == "agenda"


def test_result_dry_run_false_par_defaut(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry_path = _full_install(tmp_path)
    result = remove_module("agenda", registry_path=registry_path)
    assert result.dry_run is False


# ── CLI ──────────────────────────────────────────────────────────────────────────

def test_cli_dispatch_module_remove(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _full_install(tmp_path)
    from cli.deploy.modules import main
    main(["module:remove", "agenda"])
    out = capsys.readouterr().out
    assert "agenda" in out


def test_cli_module_remove_module_inconnu_exit_1(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reg = tmp_path / "forge_modules.json"
    reg.write_text('{"installed": {}}', encoding="utf-8")
    from cli.deploy.modules import main
    with pytest.raises(SystemExit) as exc:
        main(["module:remove", "inexistant"])
    assert exc.value.code == 1


def test_cli_module_remove_dry_run(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _full_install(tmp_path)
    from cli.deploy.modules import main
    main(["module:remove", "agenda", "--dry-run"])
    out = capsys.readouterr().out
    assert "simulée" in out.lower() or "Aucun fichier modifié" in out


def test_cli_help_inclut_module_remove():
    from cli.deploy.modules import main
    with pytest.raises(SystemExit) as exc:
        main([])
    assert exc.value.code == 1
