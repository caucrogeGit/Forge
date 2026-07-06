"""
Tests E2E-MODULE-001 — Cycle d'installation et suppression d'un module Forge.

Stratégie :
  - Un module minimal est créé dans le dossier temporaire du test (non ajouté
    comme module officiel Forge).
  - Chaque classe utilise un projet isolé via la fixture module_project.
  - Les opérations sont testées dans l'ordre : install → files → routes → remove.
  - Tout opère via CWD (monkeypatch.chdir) comme dans les scénarios réels.

Cycle testé :
  1  Découverte      — discover_module_manifests trouve le module
  2  module:install  — forge_modules.json créé avec les métadonnées
  3  module:files    — contrôleur copié dans mvc/controllers/
  4  module:routes   — mvc/routes_<module>.py généré (explicite)
                       mvc/routes.py non modifié
  5  module:remove   — fichiers supprimés, registre nettoyé
  6  Préservation    — fichiers modifiés conservés lors de la suppression
  7  project:check + project:audit passent après installation complète
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.modules import (
    ModuleAlreadyInstalledError,
    discover_module_manifests,
    generate_module_routes,
    install_module_files,
    install_module_manifest,
    load_module_manifest,
    remove_module,
)
from cli.project.project_audit import run_project_audit
from cli.project.project_check import run_project_check

_FORGE_VERSION = "2.2.0"
_MODULE_NAME = "mon_module"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _scaffold_minimal_project(root: Path) -> None:
    _write(root / "app.py", "# app")
    _write(root / "config.py", "APP_NAME = 'TestModule'\n")
    _write(
        root / "env" / "example",
        "APP_NAME=TestModule\nAPP_ROUTES_MODULE=mvc.routes\n"
        "DB_NAME=test_module_db\nDB_HOST=localhost\nDB_PORT=3306\n"
        "DB_APP_LOGIN=test_app\nDB_APP_PWD=\n"
        "DB_ADMIN_LOGIN=root\nDB_ADMIN_PWD=\n"
        "SSL_CERTFILE=cert.pem\nSSL_KEYFILE=key.pem\n",
    )
    _write(root / "env" / "dev", "DB_NAME=test_module_db\n")
    (root / "mvc" / "controllers").mkdir(parents=True)
    (root / "mvc" / "views").mkdir(parents=True)
    (root / "mvc" / "entities").mkdir(parents=True)
    _write(
        root / "mvc" / "routes.py",
        "from core.http.router import Router\nrouter = Router()\n",
    )
    _write(
        root / "mvc" / "entities" / "relations.json",
        '{"relations": []}\n',
    )


def _create_test_module(root: Path) -> None:
    """Crée un module de test minimal dans root/modules/mon_module/."""
    module_dir = root / "modules" / _MODULE_NAME
    (module_dir / "controllers").mkdir(parents=True)
    (module_dir / "module.json").write_text(
        json.dumps({
            "name": _MODULE_NAME,
            "label": "Mon module",
            "version": "0.1.0",
            "description": "Module de test E2E.",
            "provides": ["controllers", "routes"],
            "paths": {
                "controllers": "controllers",
                "routes": "routes.py",
            },
        }),
        encoding="utf-8",
    )
    _write(
        module_dir / "controllers" / f"{_MODULE_NAME}_controller.py",
        f"# {_MODULE_NAME} controller\n",
    )
    _write(
        module_dir / "routes.py",
        "def register_routes(router):\n    pass\n",
    )


def _do_install() -> None:
    manifest = load_module_manifest(Path("modules") / _MODULE_NAME / "module.json")
    install_module_manifest(manifest, f"modules/{_MODULE_NAME}")


def _do_files() -> None:
    install_module_files(_MODULE_NAME)


def _do_routes() -> None:
    generate_module_routes(_MODULE_NAME)


def _do_full_install() -> None:
    _do_install()
    _do_files()
    _do_routes()


@pytest.fixture()
def module_project(tmp_path, monkeypatch):
    """Projet minimal + module de test créé + chdir."""
    root = tmp_path / "ModuleTest"
    root.mkdir()
    _scaffold_minimal_project(root)
    _create_test_module(root)
    monkeypatch.chdir(root)
    return root


# ── Découverte ────────────────────────────────────────────────────────────────

class TestModuleDiscovery:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project

    def test_module_json_exists(self):
        assert (self.root / "modules" / _MODULE_NAME / "module.json").exists()

    def test_discover_finds_module(self):
        valid, invalid = discover_module_manifests(self.root / "modules")
        assert len(valid) == 1
        assert invalid == []

    def test_discovered_manifest_name(self):
        valid, _ = discover_module_manifests(self.root / "modules")
        assert valid[0].name == _MODULE_NAME

    def test_discovered_manifest_version(self):
        valid, _ = discover_module_manifests(self.root / "modules")
        assert valid[0].version == "0.1.0"

    def test_discovered_manifest_provides(self):
        valid, _ = discover_module_manifests(self.root / "modules")
        assert "controllers" in valid[0].provides
        assert "routes" in valid[0].provides


# ── Installation dans le registre ─────────────────────────────────────────────

class TestModuleInstall:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project
        _do_install()

    def test_registry_file_created(self):
        assert (self.root / "forge_modules.json").exists()

    def test_module_in_registry(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        assert _MODULE_NAME in data["installed"]

    def test_registry_version(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        assert data["installed"][_MODULE_NAME]["version"] == "0.1.0"

    def test_registry_source_path(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        assert "source" in data["installed"][_MODULE_NAME]

    def test_double_install_raises(self):
        manifest = load_module_manifest(Path("modules") / _MODULE_NAME / "module.json")
        with pytest.raises(ModuleAlreadyInstalledError):
            install_module_manifest(manifest, f"modules/{_MODULE_NAME}")


# ── Copie des fichiers ─────────────────────────────────────────────────────────

class TestModuleFiles:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project
        _do_install()
        _do_files()

    def test_controller_file_copied(self):
        assert (self.root / "mvc" / "controllers" / f"{_MODULE_NAME}_controller.py").exists()

    def test_controller_file_content(self):
        content = (
            self.root / "mvc" / "controllers" / f"{_MODULE_NAME}_controller.py"
        ).read_text(encoding="utf-8")
        assert _MODULE_NAME in content

    def test_registry_records_files_installed(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        files = data["installed"][_MODULE_NAME].get("files_installed", [])
        assert len(files) > 0

    def test_registry_records_controller_path(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        files = data["installed"][_MODULE_NAME].get("files_installed", [])
        assert any(f"{_MODULE_NAME}_controller.py" in f for f in files)


# ── Injection de routes ────────────────────────────────────────────────────────

class TestModuleRoutes:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project
        _do_install()
        _do_files()
        _do_routes()

    def test_dedicated_routes_file_created(self):
        assert (self.root / "mvc" / f"routes_{_MODULE_NAME}.py").exists()

    def test_dedicated_routes_file_contains_import(self):
        content = (self.root / "mvc" / f"routes_{_MODULE_NAME}.py").read_text(encoding="utf-8")
        assert "register_routes" in content

    def test_dedicated_routes_file_contains_alias(self):
        content = (self.root / "mvc" / f"routes_{_MODULE_NAME}.py").read_text(encoding="utf-8")
        assert f"register_{_MODULE_NAME}_routes" in content

    def test_module_routes_py_not_created(self):
        assert not (self.root / "mvc" / "module_routes.py").exists()

    def test_app_routes_not_modified(self):
        original = "from core.http.router import Router\nrouter = Router()\n"
        content = (self.root / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert content == original

    def test_app_routes_has_no_bridge_import(self):
        content = (self.root / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert "module_routes" not in content


# ── Suppression du module ──────────────────────────────────────────────────────

class TestModuleRemove:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project
        _do_full_install()
        remove_module(_MODULE_NAME)

    def test_controller_file_deleted(self):
        assert not (
            self.root / "mvc" / "controllers" / f"{_MODULE_NAME}_controller.py"
        ).exists()

    def test_module_removed_from_registry(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        assert _MODULE_NAME not in data["installed"]

    def test_dedicated_routes_file_exists_after_remove(self):
        # forge module:remove ne supprime pas mvc/routes_<module>.py (ticket séparé)
        # Le fichier reste sur le disque ; c'est au développeur de le retirer
        assert (self.root / "mvc" / f"routes_{_MODULE_NAME}.py").exists()

    def test_app_routes_router_preserved(self):
        content = (self.root / "mvc" / "routes.py").read_text(encoding="utf-8")
        assert "Router()" in content


# ── Préservation lors de la suppression ───────────────────────────────────────

class TestModuleRemovePreservesModified:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project
        _do_full_install()
        controller = (
            self.root / "mvc" / "controllers" / f"{_MODULE_NAME}_controller.py"
        )
        controller.write_text(
            controller.read_text(encoding="utf-8") + "# USER MODIFICATION\n",
            encoding="utf-8",
        )
        self.result = remove_module(_MODULE_NAME)

    def test_modified_controller_preserved(self):
        assert (
            self.root / "mvc" / "controllers" / f"{_MODULE_NAME}_controller.py"
        ).exists()

    def test_remove_result_reports_kept_file(self):
        kept_paths = [d.path for d in self.result.files_kept]
        assert any(f"{_MODULE_NAME}_controller.py" in p for p in kept_paths)

    def test_module_removed_from_registry_despite_kept_file(self):
        data = json.loads((self.root / "forge_modules.json").read_text(encoding="utf-8"))
        assert _MODULE_NAME not in data["installed"]


# ── project:check et project:audit ───────────────────────────────────────────

class TestModuleChecks:
    @pytest.fixture(autouse=True)
    def _setup(self, module_project):
        self.root = module_project
        _do_full_install()

    def test_project_check_no_failures(self):
        results = run_project_check(self.root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:check FAIL : {[r.detail for r in failures]}"

    def test_project_audit_no_failures(self):
        results = run_project_audit(self.root, _FORGE_VERSION)
        failures = [r for r in results if r.status == "fail"]
        assert failures == [], f"project:audit FAIL : {[r.detail for r in failures]}"
