"""Tests MODULE-SYSTEM-004 — génération explicite des routes de modules."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.modules import (
    ModuleRouteInjectionError,
    ModuleRoutesAlreadyGeneratedError,
    generate_module_routes,
    install_module_manifest,
    load_module_manifest,
)


def _write_module(root: Path, name: str = "agenda", **overrides) -> Path:
    module_dir = root / "modules" / name
    module_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "name": name,
        "label": name.capitalize(),
        "version": "0.1.0",
        "description": f"Module {name}.",
        "provides": ["routes"],
        "paths": {"routes": "routes.py"},
    }
    data.update(overrides)
    (module_dir / "module.json").write_text(json.dumps(data), encoding="utf-8")
    (module_dir / "routes.py").write_text(
        "def register_routes(router):\n"
        "    return router\n",
        encoding="utf-8",
    )
    return module_dir


def _install(root: Path, module_dir: Path, name: str = "agenda") -> Path:
    manifest = load_module_manifest(module_dir / "module.json")
    registry_path = root / "forge_modules.json"
    install_module_manifest(
        manifest,
        f"modules/{name}",
        registry_path=registry_path,
    )
    return registry_path


@pytest.mark.parametrize(
    "routes_path",
    ["/tmp/routes.py", "../routes.py", "https://example.test/routes.py"],
)
def test_generate_refuse_chemins_routes_dangereux(tmp_path, monkeypatch, routes_path):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    manifest = json.loads((module_dir / "module.json").read_text(encoding="utf-8"))
    manifest["paths"] = {"routes": routes_path}
    (module_dir / "module.json").write_text(json.dumps(manifest), encoding="utf-8")
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
                        "provides": ["routes"],
                    }
                }
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ModuleRouteInjectionError):
        generate_module_routes("agenda")


def test_generation_refuse_si_fichier_existe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    # Pré-créer le fichier cible
    target = tmp_path / "mvc" / "routes_agenda.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("# Existing\n", encoding="utf-8")

    with pytest.raises(ModuleRoutesAlreadyGeneratedError):
        generate_module_routes("agenda", registry_path=registry_path)


def test_dry_run_ne_modifie_aucun_fichier(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    app_routes = tmp_path / "mvc" / "routes.py"
    app_routes.parent.mkdir(parents=True, exist_ok=True)
    original = "from core.http.router import Router\nrouter = Router()\n"
    app_routes.write_text(original, encoding="utf-8")
    before = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }

    result = generate_module_routes("agenda", registry_path=registry_path, dry_run=True)

    after = {
        path.relative_to(tmp_path).as_posix(): path.read_text(encoding="utf-8")
        for path in tmp_path.rglob("*")
        if path.is_file()
    }
    assert before == after
    assert result.dry_run
    assert not result.generated


def test_generation_reelle_cree_fichier_dedie(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    app_routes = tmp_path / "mvc" / "routes.py"
    app_routes.parent.mkdir(parents=True, exist_ok=True)
    original = "from core.http.router import Router\nrouter = Router()\n"
    app_routes.write_text(original, encoding="utf-8")

    result = generate_module_routes("agenda", registry_path=registry_path)

    dedicated = tmp_path / "mvc" / "routes_agenda.py"
    assert dedicated.exists()
    content = dedicated.read_text(encoding="utf-8")
    assert "register_agenda_routes" in content
    assert "from modules.agenda.routes import register_routes" in content
    assert result.generated
    # mvc/routes.py n'est pas modifié
    assert app_routes.read_text(encoding="utf-8") == original


def test_generation_ne_modifie_pas_routes_py(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    app_routes = tmp_path / "mvc" / "routes.py"
    app_routes.parent.mkdir(parents=True, exist_ok=True)
    original = "from core.http.router import Router\nrouter = Router()\n"
    app_routes.write_text(original, encoding="utf-8")

    generate_module_routes("agenda", registry_path=registry_path)

    assert app_routes.read_text(encoding="utf-8") == original


def test_generation_ne_cree_pas_module_routes_py(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)

    generate_module_routes("agenda", registry_path=registry_path)

    assert not (tmp_path / "mvc" / "module_routes.py").exists()


def test_generation_reelle_ne_duplique_pas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)
    generate_module_routes("agenda", registry_path=registry_path)

    with pytest.raises(ModuleRoutesAlreadyGeneratedError):
        generate_module_routes("agenda", registry_path=registry_path)

    assert (tmp_path / "mvc" / "routes_agenda.py").exists()


def test_generation_refuse_module_non_installe(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with pytest.raises(ModuleRouteInjectionError, match="Module non installé"):
        generate_module_routes(
            "agenda",
            registry_path=tmp_path / "forge_modules.json",
        )


def test_generation_lines_to_add_contient_import(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    registry_path = _install(tmp_path, module_dir)

    result = generate_module_routes("agenda", registry_path=registry_path, dry_run=True)

    assert "from mvc.routes_agenda import register_agenda_routes" in result.lines_to_add
    assert "register_agenda_routes(router)" in result.lines_to_add


def test_generation_ne_copie_aucun_fichier_applicatif(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    module_dir = _write_module(tmp_path)
    (module_dir / "entities").mkdir()
    (module_dir / "views").mkdir()
    (module_dir / "controllers").mkdir()
    (module_dir / "entities" / "agenda.json").write_text("{}", encoding="utf-8")
    (module_dir / "views" / "index.html").write_text("", encoding="utf-8")
    (module_dir / "controllers" / "agenda_controller.py").write_text("", encoding="utf-8")
    registry_path = _install(tmp_path, module_dir)

    generate_module_routes("agenda", registry_path=registry_path)

    assert not (tmp_path / "mvc" / "entities").exists()
    assert not (tmp_path / "mvc" / "views").exists()
    assert not (tmp_path / "mvc" / "controllers").exists()
    assert (tmp_path / "mvc" / "routes_agenda.py").exists()
