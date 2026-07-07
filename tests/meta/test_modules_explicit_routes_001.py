"""Tests MODULES-EXPLICIT-ROUTES-001 — forge module:routes ne modifie jamais mvc/routes.py.

Vérifie que :
- generate_module_routes ne touche pas mvc/routes.py
- inject_module_routes n'existe plus (remplacée par generate_module_routes)
- _ensure_app_routes_bridge_content n'existe plus
- mvc/routes_<module>.py est créé (write-if-new)
- ModuleRoutesAlreadyGeneratedError est levée si le fichier existe déjà
- Les lignes à ajouter dans mvc/routes.py sont retournées dans le résultat
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

pytestmark = pytest.mark.meta


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _setup_module(tmp_path: Path, name: str = "agenda") -> Path:
    module_dir = tmp_path / "modules" / name
    module_dir.mkdir(parents=True, exist_ok=True)
    (module_dir / "module.json").write_text(
        json.dumps({
            "name": name,
            "label": name.capitalize(),
            "version": "0.1.0",
            "description": f"Module {name}.",
            "provides": ["routes"],
            "paths": {"routes": "routes.py"},
        }),
        encoding="utf-8",
    )
    (module_dir / "routes.py").write_text(
        "def register_routes(router): pass\n",
        encoding="utf-8",
    )
    return module_dir


def _install(tmp_path: Path, module_dir: Path, name: str = "agenda") -> Path:
    from core.modules import install_module_manifest, load_module_manifest
    manifest = load_module_manifest(module_dir / "module.json")
    reg_path = tmp_path / "forge_modules.json"
    install_module_manifest(manifest, f"modules/{name}", registry_path=reg_path)
    return reg_path


# ---------------------------------------------------------------------------
# TestRoutesPyNeverModified
# ---------------------------------------------------------------------------


class TestRoutesPyNeverModified:
    def test_generate_module_routes_does_not_touch_app_routes(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        app_routes = tmp_path / "mvc" / "routes" / "__init__.py"
        app_routes.parent.mkdir(parents=True, exist_ok=True)
        original = "# Original user content\n# Should not be modified\n"
        app_routes.write_text(original, encoding="utf-8")

        generate_module_routes("agenda", registry_path=registry_path)

        assert app_routes.read_text(encoding="utf-8") == original

    def test_dry_run_does_not_touch_app_routes(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        app_routes = tmp_path / "mvc" / "routes" / "__init__.py"
        app_routes.parent.mkdir(parents=True, exist_ok=True)
        original = "# user routes\n"
        app_routes.write_text(original, encoding="utf-8")

        generate_module_routes("agenda", registry_path=registry_path, dry_run=True)

        assert app_routes.read_text(encoding="utf-8") == original

    def test_no_module_routes_py_created(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        generate_module_routes("agenda", registry_path=registry_path)

        assert not (tmp_path / "mvc" / "module_routes.py").exists()


# ---------------------------------------------------------------------------
# TestGeneratedFileConvention
# ---------------------------------------------------------------------------


class TestGeneratedFileConvention:
    def test_filename_follows_convention(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path, "agenda")
        registry_path = _install(tmp_path, module_dir, "agenda")

        generate_module_routes("agenda", registry_path=registry_path)

        assert (tmp_path / "mvc" / "routes_agenda.py").exists()

    def test_generated_file_contains_module_import(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        generate_module_routes("agenda", registry_path=registry_path)

        content = (tmp_path / "mvc" / "routes_agenda.py").read_text(encoding="utf-8")
        assert "register_agenda_routes" in content

    def test_generated_file_is_valid_python(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        import ast
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        generate_module_routes("agenda", registry_path=registry_path)

        content = (tmp_path / "mvc" / "routes_agenda.py").read_text(encoding="utf-8")
        ast.parse(content)  # ne doit pas lever


# ---------------------------------------------------------------------------
# TestLinestoAdd
# ---------------------------------------------------------------------------


class TestLinesToAdd:
    def test_result_contains_import_line(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        result = generate_module_routes("agenda", registry_path=registry_path, dry_run=True)

        assert "from mvc.routes_agenda import register_agenda_routes" in result.lines_to_add

    def test_result_contains_call_line(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        result = generate_module_routes("agenda", registry_path=registry_path, dry_run=True)

        assert "register_agenda_routes(router)" in result.lines_to_add


# ---------------------------------------------------------------------------
# TestAlreadyGenerated
# ---------------------------------------------------------------------------


class TestAlreadyGenerated:
    def test_refuses_to_overwrite_existing_file(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        from core.modules.routes import ModuleRoutesAlreadyGeneratedError
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        target = tmp_path / "mvc" / "routes_agenda.py"
        target.parent.mkdir(parents=True)
        target.write_text("# Existing\n", encoding="utf-8")

        with pytest.raises(ModuleRoutesAlreadyGeneratedError):
            generate_module_routes("agenda", registry_path=registry_path)

    def test_dry_run_does_not_raise_if_file_exists(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        from core.modules import generate_module_routes
        module_dir = _setup_module(tmp_path)
        registry_path = _install(tmp_path, module_dir)

        target = tmp_path / "mvc" / "routes_agenda.py"
        target.parent.mkdir(parents=True)
        target.write_text("# Existing\n", encoding="utf-8")

        result = generate_module_routes("agenda", registry_path=registry_path, dry_run=True)
        assert result.dry_run
        assert not result.generated


# ---------------------------------------------------------------------------
# TestNoInjectionFunctionRemains
# ---------------------------------------------------------------------------


class TestNoInjectionFunctionRemains:
    def test_inject_module_routes_no_longer_exists(self):
        from core.modules import routes
        assert not hasattr(routes, "inject_module_routes"), (
            "inject_module_routes devrait être remplacée par generate_module_routes"
        )

    def test_ensure_app_routes_bridge_no_longer_exists(self):
        from core.modules import routes
        assert not hasattr(routes, "_ensure_app_routes_bridge_content"), (
            "_ensure_app_routes_bridge_content devrait être supprimée — "
            "Forge n'écrit plus dans mvc/routes.py"
        )

    def test_generate_module_routes_exists(self):
        from core.modules import routes
        assert hasattr(routes, "generate_module_routes")
        assert callable(routes.generate_module_routes)

    def test_module_routes_already_generated_error_exists(self):
        from core.modules.routes import ModuleRoutesAlreadyGeneratedError
        assert issubclass(ModuleRoutesAlreadyGeneratedError, ValueError)
