"""Tests MODULE-SYSTEM-005 — copie contrôlée des fichiers de modules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.modules import (
    ModuleFileConflictError,
    ModuleFileInstallError,
    install_module_files,
    install_module_manifest,
    load_installed_modules_registry,
    load_module_manifest,
    prepare_module_file_installation,
)


def _write_module(
    root: Path,
    name: str = "agenda",
    *,
    provides: list[str] | None = None,
    paths: dict[str, str] | None = None,
) -> Path:
    module_dir = root / "modules" / name
    module_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name}.",
        "provides": provides if provides is not None else ["entities", "controllers", "views", "docs"],
        "paths": paths
        if paths is not None
        else {
            "entities": "entities",
            "controllers": "controllers",
            "views": "views",
            "docs": "docs",
        },
    }
    (module_dir / "module.json").write_text(json.dumps(data), encoding="utf-8")
    (module_dir / "entities" / "event").mkdir(parents=True, exist_ok=True)
    (module_dir / "entities" / "event" / "event.json").write_text("{}", encoding="utf-8")
    (module_dir / "controllers").mkdir(exist_ok=True)
    (module_dir / "controllers" / "agenda_controller.py").write_text("# controller\n", encoding="utf-8")
    (module_dir / "views" / "agenda").mkdir(parents=True, exist_ok=True)
    (module_dir / "views" / "agenda" / "index.html").write_text("<h1>Agenda</h1>\n", encoding="utf-8")
    (module_dir / "docs").mkdir(exist_ok=True)
    (module_dir / "docs" / "agenda.md").write_text("# Agenda\n", encoding="utf-8")
    return module_dir


def _install(root: Path, module_dir: Path, name: str = "agenda") -> Path:
    manifest = load_module_manifest(module_dir / "module.json")
    registry_path = root / "forge_modules.json"
    install_module_manifest(manifest, f"modules/{name}", registry_path=registry_path)
    return registry_path


def _snapshot(root: Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): path.read_text(encoding="utf-8")
        for path in root.rglob("*")
        if path.is_file()
    }


def test_prepare_installation_pour_module_installe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)

    result = prepare_module_file_installation("agenda", registry_path=registry_path)

    assert result.module_name == "agenda"
    assert ("modules/agenda/entities/event/event.json", "mvc/entities/event/event.json") in result.planned_files
    assert ("modules/agenda/controllers/agenda_controller.py", "mvc/controllers/agenda_controller.py") in result.planned_files
    assert ("modules/agenda/views/agenda/index.html", "mvc/views/agenda/index.html") in result.planned_files
    assert ("modules/agenda/docs/agenda.md", "docs/modules/agenda/agenda.md") in result.planned_files
    assert not result.installed


def test_prepare_refuse_module_non_installe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ModuleFileInstallError, match="Module non installé"):
        prepare_module_file_installation("agenda", registry_path=tmp_path / "forge_modules.json")


def test_prepare_refuse_module_sans_fichier_installable(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path, provides=["routes"], paths={"routes": "routes.py"})
    (module_dir / "routes.py").write_text("", encoding="utf-8")
    registry_path = _install(tmp_path, module_dir)

    with pytest.raises(ModuleFileInstallError, match="aucun fichier installable"):
        prepare_module_file_installation("agenda", registry_path=registry_path)


def test_prepare_respecte_provides_et_paths(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(
        tmp_path,
        provides=["views"],
        paths={"views": "views"},
    )
    registry_path = _install(tmp_path, module_dir)

    result = prepare_module_file_installation("agenda", registry_path=registry_path)

    assert result.planned_files == (
        ("modules/agenda/views/agenda/index.html", "mvc/views/agenda/index.html"),
    )


@pytest.mark.parametrize(
    "path_value",
    [
        "/tmp/entities",
        "../entities",
        "https://example.test/entities",
        "file:///tmp/entities",
        "C:\\entities",
    ],
)
def test_prepare_refuse_chemins_sources_dangereux(tmp_path, monkeypatch, path_value):
    monkeypatch.chdir(tmp_path)
    _write_module(
        tmp_path,
        provides=["entities"],
        paths={"entities": path_value},
    )
    (tmp_path / "forge_modules.json").write_text(
        json.dumps(
            {
                "installed": {
                    "agenda": {
                        "name": "agenda",
                        "label": "Agenda",
                        "version": "0.1.0",
                        "description": "Module agenda.",
                        "source": "modules/agenda",
                        "provides": ["entities"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ModuleFileInstallError):
        prepare_module_file_installation("agenda")


def test_fichiers_ignores_non_copies(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path, provides=["views"], paths={"views": "views"})
    (module_dir / "views" / ".env").write_text("SECRET=1", encoding="utf-8")
    (module_dir / "views" / "agenda" / "cache.pyc").write_text("", encoding="utf-8")
    (module_dir / "views" / "agenda" / "old.bak").write_text("", encoding="utf-8")
    (module_dir / "views" / "agenda" / "temp.tmp").write_text("", encoding="utf-8")
    (module_dir / "views" / "__pycache__").mkdir()
    (module_dir / "views" / "__pycache__" / "x.pyc").write_text("", encoding="utf-8")
    registry_path = _install(tmp_path, module_dir)

    result = prepare_module_file_installation("agenda", registry_path=registry_path)

    planned_sources = [source for source, _ in result.planned_files]
    assert planned_sources == ["modules/agenda/views/agenda/index.html"]


def test_conflit_cible_detecte_et_refuse_toute_installation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    conflict = tmp_path / "mvc" / "controllers" / "agenda_controller.py"
    conflict.parent.mkdir(parents=True)
    conflict.write_text("# utilisateur\n", encoding="utf-8")
    before = _snapshot(tmp_path)

    with pytest.raises(ModuleFileConflictError) as exc:
        install_module_files("agenda", registry_path=registry_path)

    after = _snapshot(tmp_path)
    assert "mvc/controllers/agenda_controller.py" in exc.value.conflicts
    assert before == after


def test_dry_run_ne_modifie_aucun_fichier(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    before = _snapshot(tmp_path)

    result = install_module_files("agenda", registry_path=registry_path, dry_run=True)

    assert _snapshot(tmp_path) == before
    assert result.dry_run
    assert not result.installed


def test_installation_reelle_copie_fichiers_et_cree_dossiers(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)

    result = install_module_files("agenda", registry_path=registry_path)

    assert (tmp_path / "mvc" / "entities" / "event" / "event.json").exists()
    assert (tmp_path / "mvc" / "controllers" / "agenda_controller.py").exists()
    assert (tmp_path / "mvc" / "views" / "agenda" / "index.html").exists()
    assert (tmp_path / "docs" / "modules" / "agenda" / "agenda.md").exists()
    assert "mvc/controllers/agenda_controller.py" in result.copied_files
    assert result.installed


def test_installation_met_a_jour_registre_files_installed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)

    install_module_files("agenda", registry_path=registry_path)

    registry = load_installed_modules_registry(registry_path)
    files = registry["installed"]["agenda"]["files_installed"]
    assert "mvc/entities/event/event.json" in files
    assert all(not Path(path).is_absolute() for path in files)


def test_installation_ne_modifie_pas_routes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    routes = tmp_path / "mvc" / "routes" / "__init__.py"
    module_routes = tmp_path / "mvc" / "module_routes.py"
    routes.parent.mkdir(parents=True)
    routes.write_text("# routes\n", encoding="utf-8")
    module_routes.write_text("# module routes\n", encoding="utf-8")

    install_module_files("agenda", registry_path=registry_path)

    assert routes.read_text(encoding="utf-8") == "# routes\n"
    assert module_routes.read_text(encoding="utf-8") == "# module routes\n"


# --- Tests de sécurité MODULE-FILES-SECURITY-001 ---


@pytest.mark.parametrize(
    "provide,subdir,symlink_path",
    [
        ("entities", "entities", "entities/event/link.json"),
        ("controllers", "controllers", "controllers/link.py"),
        ("views", "views", "views/agenda/link.html"),
        ("docs", "docs", "docs/link.md"),
    ],
)
def test_symlink_dans_provides_refuse(tmp_path, monkeypatch, provide, subdir, symlink_path):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path, provides=[provide], paths={provide: subdir})
    external = tmp_path / "external.txt"
    external.write_text("secret", encoding="utf-8")
    (module_dir / symlink_path).symlink_to(external)
    registry_path = _install(tmp_path, module_dir)

    with pytest.raises(ModuleFileInstallError, match="ymbolique"):
        prepare_module_file_installation("agenda", registry_path=registry_path)


def test_symlink_interne_aussi_refuse(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path, provides=["entities"], paths={"entities": "entities"})
    (module_dir / "entities" / "link.json").symlink_to(
        module_dir / "entities" / "event" / "event.json"
    )
    registry_path = _install(tmp_path, module_dir)

    with pytest.raises(ModuleFileInstallError, match="ymbolique"):
        prepare_module_file_installation("agenda", registry_path=registry_path)


def test_symlink_arrete_avant_toute_copie(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    external = tmp_path / "external.txt"
    external.write_text("secret", encoding="utf-8")
    (module_dir / "entities" / "event" / "link.json").symlink_to(external)
    registry_path = _install(tmp_path, module_dir)
    before = _snapshot(tmp_path)

    with pytest.raises(ModuleFileInstallError):
        install_module_files("agenda", registry_path=registry_path)

    assert _snapshot(tmp_path) == before


def test_git_directory_ignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path, provides=["views"], paths={"views": "views"})
    git_dir = module_dir / "views" / ".git"
    git_dir.mkdir()
    (git_dir / "config").write_text("[core]\n", encoding="utf-8")
    registry_path = _install(tmp_path, module_dir)

    result = prepare_module_file_installation("agenda", registry_path=registry_path)

    planned_sources = [source for source, _ in result.planned_files]
    assert all(".git" not in s for s in planned_sources)
    assert "modules/agenda/views/agenda/index.html" in planned_sources


def test_thumbs_db_ignore(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path, provides=["views"], paths={"views": "views"})
    (module_dir / "views" / "agenda" / "Thumbs.db").write_text("", encoding="utf-8")
    registry_path = _install(tmp_path, module_dir)

    result = prepare_module_file_installation("agenda", registry_path=registry_path)

    planned_sources = [source for source, _ in result.planned_files]
    assert "modules/agenda/views/agenda/Thumbs.db" not in planned_sources
    assert "modules/agenda/views/agenda/index.html" in planned_sources


def test_cibles_limitees_aux_zones_autorisees(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)

    result = prepare_module_file_installation("agenda", registry_path=registry_path)

    allowed_prefixes = ("mvc/entities/", "mvc/controllers/", "mvc/views/", "docs/modules/")
    for _, target in result.planned_files:
        assert any(target.startswith(prefix) for prefix in allowed_prefixes), (
            f"Cible non autorisée : {target}"
        )
