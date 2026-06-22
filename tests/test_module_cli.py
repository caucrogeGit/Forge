"""Tests MODULE-SYSTEM-002/003 — commandes forge module:list et module:install."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

import forge
from cli.modules import (
    cmd_module_files,
    cmd_module_install,
    cmd_module_list,
    cmd_module_routes,
    main as modules_main,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _write_manifest(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data), encoding="utf-8")


def _valid_data(name: str = "agenda", **overrides) -> dict:
    base = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name}.",
    }
    base.update(overrides)
    return base


# ---------------------------------------------------------------------------
# Dispatch depuis forge.py
# ---------------------------------------------------------------------------


def test_module_list_reconnu(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:list"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:list"]


def test_module_list_avec_path_transmis(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:list", "--path", "modules"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:list", "--path", "modules"]


# ---------------------------------------------------------------------------
# Comportement : dossier absent ou vide
# ---------------------------------------------------------------------------


def test_dossier_absent_affiche_message(tmp_path, capsys):
    cmd_module_list(["--path", str(tmp_path / "absent")])
    output = capsys.readouterr().out
    assert "Aucun dossier de modules" in output


def test_dossier_absent_ne_cree_pas_le_dossier(tmp_path):
    absent = tmp_path / "absent"
    cmd_module_list(["--path", str(absent)])
    assert not absent.exists()


def test_dossier_vide_affiche_message(tmp_path, capsys):
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "Aucun module" in output


# ---------------------------------------------------------------------------
# Comportement : modules valides
# ---------------------------------------------------------------------------


def test_module_valide_affiche_nom_version_label(tmp_path, capsys):
    mod = tmp_path / "agenda"
    mod.mkdir()
    _write_manifest(mod / "module.json", _valid_data("agenda", label="Agenda"))
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "agenda" in output
    assert "0.1.0" in output
    assert "Agenda" in output


def test_plusieurs_modules_affiches(tmp_path, capsys):
    for name in ("agenda", "patrimoine"):
        d = tmp_path / name
        d.mkdir()
        _write_manifest(d / "module.json", _valid_data(name))
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "agenda" in output
    assert "patrimoine" in output


def test_sortie_contient_header_modules_disponibles(tmp_path, capsys):
    mod = tmp_path / "agenda"
    mod.mkdir()
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "Modules Forge disponibles" in output


# ---------------------------------------------------------------------------
# Comportement : modules invalides
# ---------------------------------------------------------------------------


def test_module_invalide_signale(tmp_path, capsys):
    mod = tmp_path / "broken"
    mod.mkdir()
    _write_manifest(mod / "module.json", {"name": "broken"})
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "broken" in output
    assert "Modules invalides" in output


def test_module_invalide_ne_bloque_pas_sortie(tmp_path, capsys):
    (tmp_path / "broken").mkdir()
    _write_manifest((tmp_path / "broken") / "module.json", {"name": "broken"})
    (tmp_path / "agenda").mkdir()
    _write_manifest((tmp_path / "agenda") / "module.json", _valid_data("agenda"))
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "agenda" in output
    assert "broken" in output


def test_seuls_invalides_affiche_message_aucun_valide(tmp_path, capsys):
    mod = tmp_path / "broken"
    mod.mkdir()
    _write_manifest(mod / "module.json", {"name": "broken"})
    cmd_module_list(["--path", str(tmp_path)])
    output = capsys.readouterr().out
    assert "Aucun module Forge valide" in output


# ---------------------------------------------------------------------------
# Comportement : la commande ne modifie rien
# ---------------------------------------------------------------------------


def test_commande_ninstalle_rien(tmp_path):
    before = sorted(str(p) for p in tmp_path.rglob("*"))
    cmd_module_list(["--path", str(tmp_path)])
    after = sorted(str(p) for p in tmp_path.rglob("*"))
    assert before == after


def test_commande_ne_modifie_aucun_fichier(tmp_path):
    mod = tmp_path / "agenda"
    mod.mkdir()
    manifest_path = mod / "module.json"
    _write_manifest(manifest_path, _valid_data("agenda"))
    before_content = manifest_path.read_text()
    cmd_module_list(["--path", str(tmp_path)])
    after_content = manifest_path.read_text()
    assert before_content == after_content


# ---------------------------------------------------------------------------
# Validation des arguments
# ---------------------------------------------------------------------------


def test_argument_inconnu_exit(tmp_path):
    with pytest.raises(SystemExit):
        cmd_module_list(["--unknown"])


def test_main_sans_args_exit():
    with pytest.raises(SystemExit):
        modules_main([])


def test_main_commande_inconnue_exit():
    with pytest.raises(SystemExit):
        modules_main(["module:unknown"])


# ---------------------------------------------------------------------------
# Dispatch depuis forge.py — module:install
# ---------------------------------------------------------------------------


def test_module_install_reconnu(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:install", "agenda"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:install", "agenda"]


def test_module_install_avec_path_transmis(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:install", "agenda", "--path", "modules"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:install", "agenda", "--path", "modules"]


def test_module_install_dry_run_transmis(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:install", "agenda", "--dry-run"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:install", "agenda", "--dry-run"]


def test_module_routes_reconnu(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:routes", "agenda"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:routes", "agenda"]


def test_module_routes_dry_run_transmis(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:routes", "agenda", "--dry-run"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:routes", "agenda", "--dry-run"]


# ---------------------------------------------------------------------------
# Comportement : module introuvable
# ---------------------------------------------------------------------------


def test_module_introuvable_affiche_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cmd_module_install(["absent", "--path", "modules"])
    output = capsys.readouterr().out
    assert "introuvable" in output.lower()
    assert "absent" in output


# ---------------------------------------------------------------------------
# Comportement : module invalide
# ---------------------------------------------------------------------------


def test_module_invalide_affiche_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "broken"
    mod.mkdir(parents=True)
    (mod / "module.json").write_text('{"name": "broken"}', encoding="utf-8")
    with pytest.raises(SystemExit):
        cmd_module_install(["broken", "--path", "modules"])
    output = capsys.readouterr().out
    assert "invalide" in output.lower() or "broken" in output


# ---------------------------------------------------------------------------
# Comportement : installation réelle
# ---------------------------------------------------------------------------


def test_module_installe_affiche_nom_version_label(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda", label="Agenda"))
    cmd_module_install(["agenda", "--path", "modules"])
    output = capsys.readouterr().out
    assert "agenda" in output
    assert "0.1.0" in output
    assert "Agenda" in output


def test_module_installe_cree_registre(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    cmd_module_install(["agenda", "--path", "modules"])
    assert (tmp_path / "forge_modules.json").exists()


def test_module_installe_affiche_registre_mis_a_jour(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    cmd_module_install(["agenda", "--path", "modules"])
    output = capsys.readouterr().out
    assert "forge_modules.json" in output


# ---------------------------------------------------------------------------
# Comportement : dry-run
# ---------------------------------------------------------------------------


def test_dry_run_naffecte_aucun_fichier(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    before = set(tmp_path.rglob("*"))
    cmd_module_install(["agenda", "--path", "modules", "--dry-run"])
    after = set(tmp_path.rglob("*"))
    assert before == after


def test_dry_run_affiche_message_simule(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    cmd_module_install(["agenda", "--path", "modules", "--dry-run"])
    output = capsys.readouterr().out
    assert "simulé" in output.lower() or "simulation" in output.lower()
    assert "Aucun fichier modifié" in output


# ---------------------------------------------------------------------------
# Comportement : module déjà installé
# ---------------------------------------------------------------------------


def test_module_deja_installe_affiche_message(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    cmd_module_install(["agenda", "--path", "modules"])
    capsys.readouterr()
    with pytest.raises(SystemExit):
        cmd_module_install(["agenda", "--path", "modules"])
    output = capsys.readouterr().out
    assert "déjà installé" in output


# ---------------------------------------------------------------------------
# Comportement : pas de copie / pas d'injection
# ---------------------------------------------------------------------------


def test_install_ne_copie_pas_fichiers_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    (mod / "controllers").mkdir()
    (mod / "controllers" / "agenda_controller.py").write_text("# code", encoding="utf-8")
    mvc_dir = tmp_path / "mvc"
    mvc_dir.mkdir()
    cmd_module_install(["agenda", "--path", "modules"])
    assert not list(mvc_dir.rglob("agenda_controller.py"))


def test_install_ninjecte_aucune_route(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    _write_manifest(mod / "module.json", _valid_data("agenda"))
    mvc_dir = tmp_path / "mvc"
    mvc_dir.mkdir()
    routes = mvc_dir / "routes.py"
    routes.write_text("# app routes\n", encoding="utf-8")
    before = routes.read_text()
    cmd_module_install(["agenda", "--path", "modules"])
    assert routes.read_text() == before


# ---------------------------------------------------------------------------
# Comportement : module:files
# ---------------------------------------------------------------------------


def test_module_files_reconnu(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:files", "agenda"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:files", "agenda"]


def test_module_files_dry_run_transmis(monkeypatch):
    captured = {}

    def fake_modules_main(args):
        captured["args"] = args

    monkeypatch.setattr(sys, "argv", ["forge", "module:files", "agenda", "--dry-run"])
    monkeypatch.setattr(forge, "modules_main", fake_modules_main)
    forge.main()
    assert captured["args"] == ["module:files", "agenda", "--dry-run"]


def _write_files_module(tmp_path: Path, *, provides_files: bool = True) -> Path:
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    data = _valid_data("agenda")
    if provides_files:
        data["provides"] = ["entities", "controllers", "views", "docs"]
        data["paths"] = {
            "entities": "entities",
            "controllers": "controllers",
            "views": "views",
            "docs": "docs",
        }
        (mod / "entities" / "event").mkdir(parents=True)
        (mod / "entities" / "event" / "event.json").write_text("{}", encoding="utf-8")
        (mod / "controllers").mkdir()
        (mod / "controllers" / "agenda_controller.py").write_text("# controller\n", encoding="utf-8")
        (mod / "views" / "agenda").mkdir(parents=True)
        (mod / "views" / "agenda" / "index.html").write_text("<h1>Agenda</h1>\n", encoding="utf-8")
        (mod / "docs").mkdir()
        (mod / "docs" / "agenda.md").write_text("# Agenda\n", encoding="utf-8")
    _write_manifest(mod / "module.json", data)
    return mod


def test_module_files_dry_run_affiche_copies_sans_ecrire(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_files_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])
    before = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_text(encoding="utf-8"))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )

    cmd_module_files(["agenda", "--dry-run"])

    after = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_text(encoding="utf-8"))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    output = capsys.readouterr().out
    assert before == after
    assert "Installation simulée des fichiers" in output
    assert "modules/agenda/controllers/agenda_controller.py -> mvc/controllers/agenda_controller.py" in output
    assert "Aucun fichier modifié" in output


def test_module_files_copie_fichiers_attendus(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_files_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])

    cmd_module_files(["agenda"])

    output = capsys.readouterr().out
    assert "Fichiers du module installés" in output
    assert (tmp_path / "mvc" / "entities" / "event" / "event.json").exists()
    assert (tmp_path / "mvc" / "controllers" / "agenda_controller.py").exists()
    assert (tmp_path / "mvc" / "views" / "agenda" / "index.html").exists()
    assert (tmp_path / "docs" / "modules" / "agenda" / "agenda.md").exists()


def test_module_files_module_non_installe_message_clair(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cmd_module_files(["agenda"])
    output = capsys.readouterr().out
    assert "Module non installé : agenda" in output
    assert "forge module:install agenda" in output


def test_module_files_conflit_message_clair(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_files_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])
    conflict = tmp_path / "mvc" / "controllers" / "agenda_controller.py"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("# utilisateur\n", encoding="utf-8")

    with pytest.raises(SystemExit):
        cmd_module_files(["agenda"])

    output = capsys.readouterr().out
    assert "Installation refusée" in output
    assert "mvc/controllers/agenda_controller.py" in output
    assert "Aucun fichier" in output
    assert conflict.read_text(encoding="utf-8") == "# utilisateur\n"


def test_module_files_module_sans_fichiers_installables_message_clair(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_files_module(tmp_path, provides_files=False)
    cmd_module_install(["agenda", "--path", "modules"])
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cmd_module_files(["agenda"])

    output = capsys.readouterr().out
    assert "aucun fichier installable" in output


def test_module_files_ne_modifie_pas_routes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    _write_files_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])
    routes = tmp_path / "mvc" / "routes.py"
    module_routes = tmp_path / "mvc" / "module_routes.py"
    routes.parent.mkdir(parents=True)
    routes.write_text("# routes\n", encoding="utf-8")
    module_routes.write_text("# module routes\n", encoding="utf-8")

    cmd_module_files(["agenda"])

    assert routes.read_text(encoding="utf-8") == "# routes\n"
    assert module_routes.read_text(encoding="utf-8") == "# module routes\n"


# ---------------------------------------------------------------------------
# Comportement : module:routes
# ---------------------------------------------------------------------------


def _write_routes_module(tmp_path: Path, *, provides_routes: bool = True) -> Path:
    mod = tmp_path / "modules" / "agenda"
    mod.mkdir(parents=True)
    data = _valid_data("agenda")
    if provides_routes:
        data["provides"] = ["routes"]
        data["paths"] = {"routes": "routes.py"}
        (mod / "routes.py").write_text(
            "def register_routes(router):\n"
            "    return router\n",
            encoding="utf-8",
        )
    _write_manifest(mod / "module.json", data)
    return mod


def _write_routes_py(tmp_path: Path) -> None:
    routes = tmp_path / "mvc" / "routes.py"
    routes.parent.mkdir(parents=True, exist_ok=True)
    routes.write_text(
        "from core.http.router import Router\n\nrouter = Router()\n",
        encoding="utf-8",
    )


def test_module_routes_dry_run_necrit_rien(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_routes_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])
    _write_routes_py(tmp_path)
    before = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_text(encoding="utf-8"))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )

    cmd_module_routes(["agenda", "--dry-run"])

    after = sorted(
        (path.relative_to(tmp_path).as_posix(), path.read_text(encoding="utf-8"))
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    output = capsys.readouterr().out
    assert before == after
    assert "Génération simulée" in output
    assert "Aucun fichier modifié" in output


def test_module_routes_injecte_si_module_installe(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_routes_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])
    _write_routes_py(tmp_path)

    cmd_module_routes(["agenda"])

    output = capsys.readouterr().out
    assert "Fichier de routes généré" in output
    assert "mvc/routes_agenda.py" in output
    assert "Pour activer ces routes" in output
    assert (tmp_path / "mvc" / "routes_agenda.py").exists()


def test_module_routes_module_non_installe_message_clair(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(SystemExit):
        cmd_module_routes(["agenda"])
    output = capsys.readouterr().out
    assert "Module non installé : agenda" in output
    assert "forge module:install agenda" in output


def test_module_routes_module_sans_routes_message_clair(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_routes_module(tmp_path, provides_routes=False)
    cmd_module_install(["agenda", "--path", "modules"])
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cmd_module_routes(["agenda"])

    output = capsys.readouterr().out
    assert "ne déclare pas de routes" in output


def test_module_routes_deja_injectees_message_clair(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    _write_routes_module(tmp_path)
    cmd_module_install(["agenda", "--path", "modules"])
    _write_routes_py(tmp_path)
    cmd_module_routes(["agenda"])
    capsys.readouterr()

    with pytest.raises(SystemExit):
        cmd_module_routes(["agenda"])

    output = capsys.readouterr().out
    assert "mvc/routes_agenda.py existe déjà" in output


def test_module_routes_ninstalle_pas_fichiers_module(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    mod = _write_routes_module(tmp_path)
    (mod / "controllers").mkdir()
    (mod / "controllers" / "agenda_controller.py").write_text("# code", encoding="utf-8")
    (mod / "views").mkdir()
    (mod / "views" / "index.html").write_text("", encoding="utf-8")
    cmd_module_install(["agenda", "--path", "modules"])
    _write_routes_py(tmp_path)

    cmd_module_routes(["agenda"])

    assert not (tmp_path / "mvc" / "controllers").exists()
    assert not (tmp_path / "mvc" / "views").exists()
